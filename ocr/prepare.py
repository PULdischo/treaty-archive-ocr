#!/usr/bin/env python3
"""Step 1: turn PDFs and image files into one PNG per page plus a page manifest.

Runs on CPU (a login node is fine for a few thousand pages; use a CPU job for more).

    python ocr/prepare.py data/pdfs                 # every PDF/image under data/pdfs
    python ocr/prepare.py data/pdfs --dpi 200       # sharper images, more image tokens

Writes
    data/pages/<doc_id>/<page_id>.png
    data/pages.jsonl     one row per page:
        page_id, doc_id, source, page, n_pages, image, width, height, embedded_text

`embedded_text` is the text layer already inside the PDF (for example Acrobat
OCR added by the library). We keep it as a baseline to compare the VLMs against.
Re-running is safe: pages already in the manifest are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageFile

Image.MAX_IMAGE_PIXELS = None          # archival scans can exceed Pillow's default size limit
ImageFile.LOAD_TRUNCATED_IMAGES = True  # read what we can from a damaged file instead of crashing

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".jp2", ".bmp", ".webp"}


def doc_id_for(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(rel)).strip("_")


def rel(path: Path) -> str:
    """Path relative to the project folder, so the folder can be moved or copied."""
    r = os.path.relpath(path)
    return str(path) if r.startswith("..") else r


def is_pdf(path: Path) -> bool:
    with open(path, "rb") as fh:
        return fh.read(5) == b"%PDF-"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="folder of PDFs and/or page images (searched recursively)")
    ap.add_argument("--out", default="data", help="output folder (default: data)")
    ap.add_argument("--dpi", type=int, default=150, help="PDF render resolution (default 150)")
    ap.add_argument("--max-side", type=int, default=2000,
                    help="shrink page images whose longest side is bigger than this (default 2000 px)")
    a = ap.parse_args()

    root = Path(a.input).resolve()
    out = Path(a.out)
    (out / "pages").mkdir(parents=True, exist_ok=True)
    manifest = out / "pages.jsonl"
    done = set()
    if manifest.exists():
        done = {json.loads(l)["page_id"] for l in manifest.open() if l.strip()}

    files = sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith("."))
    # Page images in the same folder form ONE document, pages in file-name order
    # (e.g. data/nara/<na_id>/0001.jpg, 0002.jpg). Each PDF is its own document.
    image_groups: dict[Path, list[Path]] = {}
    pdfs = []
    for f in files:
        if f.suffix.lower() in IMAGE_EXT:
            image_groups.setdefault(f.parent, []).append(f)
        elif f.suffix.lower() not in {".json", ".txt", ".csv", ".md", ".part"}:
            pdfs.append(f)
    n_new = 0
    with manifest.open("a") as mf:
        for folder, imgs in image_groups.items():
            did = doc_id_for(folder, root) if folder != root else root.name
            ddir = out / "pages" / did
            rows = []
            for i, f in enumerate(imgs, start=1):
                pid = f"{did}_p{i:04d}"
                if pid in done:
                    continue
                try:
                    img = Image.open(f).convert("RGB")
                except Exception as exc:
                    print(f"SKIP {f}: {exc}", file=sys.stderr)
                    continue
                if max(img.size) > a.max_side:
                    img.thumbnail((a.max_side, a.max_side), Image.LANCZOS)
                ddir.mkdir(parents=True, exist_ok=True)
                dest = ddir / f"{pid}.png"
                img.save(dest)
                rows.append(dict(page_id=pid, doc_id=did, source=rel(f), page=i, n_pages=len(imgs), image=str(dest),
                                 width=img.width, height=img.height, embedded_text=""))
            for r in rows:
                mf.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_new += len(rows)
            if rows:
                print(f"{did}: {len(rows)} pages")

        for f in pdfs:
            did = doc_id_for(f, root)
            ddir = out / "pages" / did
            rows = []
            try:
                if is_pdf(f):
                    doc = pymupdf.open(f)
                    for i, page in enumerate(doc, start=1):
                        pid = f"{did}_p{i:04d}"
                        if pid in done:
                            continue
                        ddir.mkdir(parents=True, exist_ok=True)
                        pix = page.get_pixmap(dpi=a.dpi)
                        dest = ddir / f"{pid}.png"
                        pix.save(dest)
                        rows.append(dict(page_id=pid, doc_id=did, source=rel(f), page=i, n_pages=doc.page_count,
                                         image=str(dest), width=pix.width, height=pix.height,
                                         embedded_text=page.get_text().strip()))
                else:
                    continue
            except Exception as exc:  # keep going; report bad files at the end of the log
                print(f"SKIP {f}: {exc}", file=sys.stderr)
                continue
            for r in rows:
                mf.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_new += len(rows)
            if rows:
                print(f"{did}: {len(rows)} pages")
    print(f"done: {n_new} new pages, manifest {manifest}")


if __name__ == "__main__":
    main()
