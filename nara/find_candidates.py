#!/usr/bin/env python3
"""Find likely relevant presidential-library records in the National Archives Catalog.

    python nara/find_candidates.py                       # writes nara/candidates.csv
    python nara/find_candidates.py --min-score 3         # stricter
    python nara/find_candidates.py --libraries JC WJC    # only Carter and Clinton

How it works
------------
nara/index/ holds a compact copy of the catalog descriptions for the Carter,
Reagan, Bush, Clinton, Bush and Obama libraries (one row per series, folder
["fileUnit"] or item, plus one row per scanned page/file). It was extracted from
the public NARA Catalog dataset on AWS (s3://nara-national-archives-catalog).

Every record's title, scope note, and the titles of its parent series and
folder are matched against the patterns in nara/search_terms.csv. Each match
adds that term's weight to the record's score. Records scoring at least
--min-score are written out. Edit search_terms.csv to add agreements or
change weights, then re-run.

Output columns (nara/candidates.csv)
------------------------------------
keep            pre-filled "y" for textual records and "n" for photographs, audio,
                video and social-media posts. Change to "n" (or delete the row) for
                anything you don't want. download.py only fetches rows marked "y".
notes           empty, for your own notes
score           sum of matched term weights
agreements      agreement terms matched;  process: ratification/implementation terms
generic         generic terms matched (treaty, accord, negotiations)
                (terms of kind "exclude" have negative weights and lower the score)
library, president, na_id, level (series / fileUnit = folder / item = document)
title, series_title, folder_title, collection, creator, date
textual         "y" if the catalog describes the record as textual (documents, not photos)
n_files         number of scanned files in the catalog (0 = described but not digitized)
has_nara_ocr    the catalog already has NARA's own OCR text for some files
catalog_url     link to the record on catalog.archives.gov
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
LIBRARIES = {"JC": "Carter", "RR": "Reagan", "GB": "George H. W. Bush", "WJC": "Clinton",
             "GWB": "George W. Bush", "BHO": "Obama"}


def load_terms(path: Path) -> list[dict]:
    terms = []
    for row in csv.DictReader(open(path, newline="")):
        flags = 0 if row["case_sensitive"].strip().lower().startswith("y") else re.IGNORECASE
        terms.append(dict(label=row["label"], kind=row["kind"], weight=float(row["weight"]),
                          rx=re.compile(row["regex"], flags)))
    return terms


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", default=str(HERE / "index"))
    ap.add_argument("--terms", default=str(HERE / "search_terms.csv"))
    ap.add_argument("--out", default=str(HERE / "candidates.csv"))
    ap.add_argument("--min-score", type=float, default=2)
    ap.add_argument("--libraries", nargs="+", default=list(LIBRARIES), choices=list(LIBRARIES))
    ap.add_argument("--digitized-only", action="store_true", help="drop records with no scanned files")
    a = ap.parse_args()

    terms = load_terms(Path(a.terms))
    rx_src = "^coll_(" + "|".join(a.libraries) + ")-"
    con = duckdb.connect()
    con.execute(f"""create view rec as select * from read_parquet('{a.index}/records/*.parquet', union_by_name=true)
                    where regexp_matches(source, '{rx_src}')""")
    con.execute(f"""create view img as select * from read_parquet('{a.index}/images/*.parquet', union_by_name=true)
                    where regexp_matches(source, '{rx_src}')""")
    rows = con.execute("""
        select r.na_id, r.source, r.level, r.title, coalesce(r.scope_note, '') as scope_note,
               coalesce(s.title, '') as series_title, coalesce(f.title, '') as folder_title,
               coalesce(r.creator_heading, '') as creator, coalesce(r.valid_time, '') as date,
               coalesce(r.is_textual, false) as is_textual, coalesce(i.n_files, 0) as n_files, coalesce(i.n_ocr, 0) > 0 as has_nara_ocr
        from rec r
        left join (select na_id, title from rec) s on s.na_id = r.parent_series
        left join (select na_id, title from rec) f on f.na_id = r.parent_file_unit
        left join (select na_id, count(*) as n_files, sum(case when ocr_len > 0 then 1 else 0 end) as n_ocr
                   from img group by na_id) i on i.na_id = r.na_id
    """).fetchall()
    cols = ["na_id", "source", "level", "title", "scope_note", "series_title", "folder_title", "creator", "date",
            "is_textual", "n_files", "has_nara_ocr"]
    print(f"searching {len(rows):,} records with {len(terms)} terms")

    out = []
    for r in map(lambda t: dict(zip(cols, t)), rows):
        if a.digitized_only and not r["n_files"]:
            continue
        text = " | ".join([r["title"] or "", r["scope_note"], r["series_title"], r["folder_title"]])
        hits = [t for t in terms if t["rx"].search(text)]
        score = sum(t["weight"] for t in hits)
        if score < a.min_score:
            continue
        lib = r["source"].split("_", 1)[1].split("-", 1)[0]
        pick = lambda kind: "; ".join(t["label"] for t in hits if t["kind"] == kind)  # noqa: E731
        out.append(dict(
            keep="y" if r["is_textual"] else "n", notes="", score=score, agreements=pick("agreement"), process=pick("process"),
            generic=pick("generic"), library=lib, president=LIBRARIES[lib], na_id=r["na_id"], level=r["level"],
            title=r["title"], series_title=r["series_title"], folder_title=r["folder_title"],
            collection=r["source"].removeprefix("coll_"), creator=r["creator"], date=r["date"],
            textual="y" if r["is_textual"] else "n", n_files=r["n_files"], has_nara_ocr="y" if r["has_nara_ocr"] else "",
            catalog_url=f"https://catalog.archives.gov/id/{r['na_id']}"))

    order = list(LIBRARIES)
    out.sort(key=lambda d: (order.index(d["library"]), d["textual"] != "y", -d["score"], d["series_title"], d["title"] or ""))
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]) if out else ["keep"])
        w.writeheader()
        w.writerows(out)

    print(f"{len(out):,} candidates -> {a.out}")
    print(f"{'library':20s} {'records':>8s} {'digitized':>9s} {'files':>8s}")
    for lib in order:
        sel = [d for d in out if d["library"] == lib]
        if sel:
            print(f"{LIBRARIES[lib]:20s} {len(sel):8,d} {sum(1 for d in sel if d['n_files']):9,d} "
                  f"{sum(d['n_files'] for d in sel):8,d}")


if __name__ == "__main__":
    main()
