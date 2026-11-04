#!/usr/bin/env python3
"""Step 4: turn one model's results into files people can read and analyse.

    python ocr/export.py --model qwen3vl-8b

Writes
    exports/<model>/<doc_id>.md   one file per PDF, a "## Page N" heading per page
    exports/<model>/pages.csv     one row per page: doc_id, page, page_id, source, text, flag

`flag` is "truncated" when the model hit its output limit on that page. That
usually means it got stuck repeating itself, so check those pages by eye.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--pages-file", default="data/pages.jsonl")
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="exports")
    a = ap.parse_args()

    res = {}
    for f in (Path(a.results) / a.model).glob("*.jsonl"):
        for r in map(json.loads, f.open()):
            res[r["page_id"]] = r
    by_doc = defaultdict(list)
    for p in map(json.loads, open(a.pages_file)):
        if p["page_id"] in res:
            by_doc[p["doc_id"]].append(p)

    out = Path(a.out) / a.model
    out.mkdir(parents=True, exist_ok=True)
    n_trunc = 0
    with (out / "pages.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["doc_id", "page", "page_id", "source", "text", "flag"])
        for did, pages in sorted(by_doc.items()):
            pages.sort(key=lambda p: p["page"])
            md = [f"# {did}\n", f"Source: `{pages[0]['source']}`  \nOCR model: {a.model}\n"]
            for p in pages:
                r = res[p["page_id"]]
                flag = "truncated" if r["finish_reason"] == "length" else ""
                n_trunc += bool(flag)
                md.append(f"\n## Page {p['page']}{'  (WARNING: output truncated)' if flag else ''}\n\n{r['text']}\n")
                w.writerow([did, p["page"], p["page_id"], p["source"], r["text"], flag])
            (out / f"{did}.md").write_text("".join(md), encoding="utf-8")
    print(f"{len(by_doc)} documents, {len(res)} pages, {n_trunc} truncated -> {out}")


if __name__ == "__main__":
    main()
