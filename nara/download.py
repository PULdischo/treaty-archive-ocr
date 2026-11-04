#!/usr/bin/env python3
"""Download the scanned files for the records you kept in nara/candidates.csv.

Needs the internet, so run it on a login node (della-gpu) or a vis node,
never inside a Slurm job.

    python nara/download.py --dry-run          # just count files, download nothing
    python nara/download.py                    # download rows with keep = y
    python nara/download.py --csv my_list.csv  # any CSV with keep and na_id columns

For each kept record with scans, writes
    data/nara/<na_id>/0001.jpg, 0002.jpg ... (or .pdf)   in catalog page order
    data/nara/<na_id>/record.json                         catalog metadata for citation
Then run:  python ocr/prepare.py data/nara
Each <na_id> folder becomes one document (doc_id = na_id) in the OCR pipeline.

When a record has a PDF as well as page images, only the PDF is fetched
(use --all-files for both). Re-running skips files already downloaded. Files
are public; no account or key is needed. If NARA has moved a file since the
index was built, its current location is looked up in the catalog.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse

import duckdb

HERE = Path(__file__).resolve().parent
KEEP_VALUES = {"y", "yes", "1", "true", "x"}
WANTED_TYPES = ("Image (JPG)", "Image (TIFF)", "Image (PNG)", "Image (JP2)", "Portable Document File (PDF)")


S3_LZ = re.compile(r"^https://s3(?:\.[a-z0-9-]+)?\.amazonaws\.com/NARAprodstorage/lz/")


def url_options(url: str) -> list[str]:
    """The index stores NARA's S3 URLs. Presidential-library files there now return
    403 Forbidden, but the catalog website serves the same files under /medialz/."""
    alt = S3_LZ.sub("https://catalog.archives.gov/medialz/", url)
    return [alt, url] if alt != url else [url]


_catalog_cache: dict[str, dict[str, str]] = {}
_catalog_lock = threading.Lock()


def catalog_urls(na_id: str) -> dict[str, str]:
    """Ask the catalog for a record's current file URLs, keyed by lower-case file name.
    Older files (".../opastorage/...") have moved to new paths that can't be worked
    out from the old URL, so we look them up. One request per record, cached."""
    with _catalog_lock:
        if na_id in _catalog_cache:
            return _catalog_cache[na_id]
    found = {}
    try:
        api = f"https://catalog.archives.gov/proxy/records/search?naId_is={na_id}&allowLegacyOrgNames=true"
        req = urllib.request.Request(api, headers={"User-Agent": "treaty-archive-ocr/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            hits = json.loads(r.read())["body"]["hits"]["hits"]
        for o in (hits[0]["_source"]["record"].get("digitalObjects") or []) if hits else []:
            found[Path(unquote(urlparse(o["objectUrl"]).path)).name.lower()] = o["objectUrl"]
    except Exception:
        pass
    with _catalog_lock:
        _catalog_cache[na_id] = found
    return found


def fetch(url: str, dest: Path, na_id: str, retries: int = 3) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    tmp = dest.with_suffix(dest.suffix + ".part")
    err = ""
    for attempt in range(retries):
        options = url_options(url)
        if attempt > 0 or err:  # the stored URL failed: ask the catalog where the file is now
            new = catalog_urls(na_id).get(Path(unquote(urlparse(url).path)).name.lower())
            if new:
                options = [new] + options
        for u in options:
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "treaty-archive-ocr/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as fh:
                    shutil.copyfileobj(r, fh)
                tmp.rename(dest)
                return "ok"
            except Exception as exc:  # try the other URL form, then retry
                err = f"{u} {exc}"
        time.sleep(2)
    tmp.unlink(missing_ok=True)
    return f"fail {err}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=str(HERE / "candidates.csv"))
    ap.add_argument("--index", default=str(HERE / "index"))
    ap.add_argument("--out", default="data/nara")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-files", type=int, default=0, help="stop after this many files (0 = no limit)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all-files", action="store_true",
                    help="also fetch page images for records that have a PDF (by default only the PDF)")
    a = ap.parse_args()

    kept = {r["na_id"]: r for r in csv.DictReader(open(a.csv, newline="", encoding="utf-8"))
            if r.get("keep", "").strip().lower() in KEEP_VALUES}
    con = duckdb.connect()
    con.execute(f"create view img as select * from read_parquet('{a.index}/images/*.parquet', union_by_name=true)")
    con.execute("create temp table ids(na_id varchar)")
    con.executemany("insert into ids values (?)", [(i,) for i in kept])
    objs = con.execute(f"""
        select na_id, page, object_url, object_type from img
        where na_id in (select na_id from ids) and object_type in {WANTED_TYPES}
        order by na_id, page
    """).fetchall()

    if not a.all_files:
        # Many records have both a PDF and page images of the same pages; keep just
        # the PDF so nothing is OCR'd twice.
        has_pdf = {o[0] for o in objs if "PDF" in o[3]}
        objs = [o for o in objs if o[0] not in has_pdf or "PDF" in o[3]]
    jobs = []
    n_per = {}
    for na_id, page, url, otype in objs:
        n_per[na_id] = n_per.get(na_id, 0) + 1
        ext = Path(unquote(urlparse(url).path)).suffix.lower() or (".pdf" if "PDF" in otype else ".jpg")
        jobs.append((url, Path(a.out) / na_id / f"{n_per[na_id]:04d}{ext}", na_id))
    if a.max_files:
        jobs = jobs[: a.max_files]

    print(f"{len(kept):,} records kept; {len(n_per):,} have scans; {len(jobs):,} files to fetch")
    if a.dry_run or not jobs:
        return

    for na_id in {n for _, _, n in jobs}:
        folder = Path(a.out) / na_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "record.json").write_text(json.dumps(kept[na_id], indent=2, ensure_ascii=False))

    counts = {"ok": 0, "skip": 0, "fail": 0}
    failures = []
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(fetch, u, d, n) for u, d, n in jobs]
        for k, f in enumerate(as_completed(futs), 1):
            res = f.result()
            key = res.split()[0]
            counts[key] += 1
            if key == "fail":
                failures.append(res)
            if k % 200 == 0:
                print(f"  {k}/{len(jobs)} {counts}", flush=True)
    print(f"done {counts}")
    if failures:
        Path(a.out, "_failures.txt").write_text("\n".join(failures) + "\n")
        print(f"failures listed in {a.out}/_failures.txt; re-run to retry")


if __name__ == "__main__":
    main()
