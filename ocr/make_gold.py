#!/usr/bin/env python3
"""Pick pages for a hand-corrected "gold" set, used to measure OCR accuracy.

    python ocr/make_gold.py --sample 25                  # random 25 pages (fixed seed)
    python ocr/make_gold.py --pages p1_id p2_id ...      # chosen pages
    python ocr/make_gold.py --sample 25 --prefill none   # empty files, type from scratch

Writes gold/pages.txt (the page list) and gold/<page_id>.txt for each page,
pre-filled with the PDF's own embedded text by default. Open each .txt next to
its image (path listed in gold/pages.tsv) and correct it by hand until it
matches the page exactly. See README.md, "Making the gold set".

Pre-filling from one of the VLMs would bias the comparison toward that model,
so the default is the embedded text, which none of the candidates produced.
Existing gold files are never overwritten.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages-file", default="data/pages.jsonl")
    ap.add_argument("--gold", default="gold")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sample", type=int, help="number of random pages")
    g.add_argument("--pages", nargs="+", help="explicit page_ids")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--min-chars", type=int, default=50,
                    help="when sampling, skip pages whose embedded text is shorter (near-blank pages)")
    ap.add_argument("--prefill", default="embedded", choices=["embedded", "none"])
    a = ap.parse_args()

    pages = {p["page_id"]: p for p in map(json.loads, open(a.pages_file)) if p}
    if a.pages:
        chosen = [pages[i] for i in a.pages]
    else:
        pool = [p for p in pages.values() if len(p["embedded_text"]) >= a.min_chars] or list(pages.values())
        chosen = sorted(random.Random(a.seed).sample(pool, min(a.sample, len(pool))), key=lambda p: p["page_id"])

    gold = Path(a.gold)
    gold.mkdir(exist_ok=True)
    (gold / "pages.txt").write_text("".join(p["page_id"] + "\n" for p in chosen))
    (gold / "pages.tsv").write_text("page_id\timage\n" + "".join(f"{p['page_id']}\t{p['image']}\n" for p in chosen))
    for p in chosen:
        f = gold / f"{p['page_id']}.txt"
        if not f.exists():
            f.write_text(p["embedded_text"] + "\n" if a.prefill == "embedded" else "")
    print(f"{len(chosen)} gold pages listed in {gold/'pages.txt'}; correct each {gold}/<page_id>.txt by hand")


if __name__ == "__main__":
    main()
