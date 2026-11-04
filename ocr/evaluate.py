#!/usr/bin/env python3
"""Step 3: score every model against the hand-corrected gold pages.

    python ocr/evaluate.py
    python ocr/evaluate.py --casefold      # ignore upper/lower case differences

Reports character error rate (CER) and word error rate (WER) per model, plus
the PDF's embedded text as a baseline ("embedded"). Lower is better; 0.05 CER
means about 5 wrong characters per 100.

Before comparing, both texts are normalised so formatting choices don't count
as errors: HTML/markdown markup is removed, our [HANDWRITTEN: x] / [STAMP: x] /
[STRUCK: x] labels are reduced to x, [ILLEGIBLE] and [BLANK PAGE] are dropped,
and all whitespace (line breaks included) becomes single spaces.

Writes results/eval_pages.csv with the score of every model on every page.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from rapidfuzz.distance import Levenshtein

sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import html_to_text, strip_front_matter  # noqa: E402

LABEL_RE = re.compile(r"\[(?:HANDWRITTEN|STAMP|STRUCK)[^:\]]*:\s*(.*?)\]", re.DOTALL)


def normalise(text: str, casefold: bool = False) -> str:
    text = strip_front_matter(text)
    text = html_to_text(text)
    text = LABEL_RE.sub(r"\1", text)
    text = re.sub(r"\[(ILLEGIBLE|BLANK PAGE)\]", " ", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)      # markdown headings
    text = re.sub(r"\*\*|__|\|", " ", text)                  # bold markers, table pipes
    text = re.sub(r"(?m)^\s*-{3,}\s*$", " ", text)           # table rules / hr
    text = text.replace("­", "")                        # soft hyphens
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold() if casefold else text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", default="gold")
    ap.add_argument("--results", default="results")
    ap.add_argument("--pages-file", default="data/pages.jsonl")
    ap.add_argument("--casefold", action="store_true")
    a = ap.parse_args()

    gold_ids = [l.strip() for l in open(Path(a.gold) / "pages.txt") if l.strip()]
    gold = {i: normalise((Path(a.gold) / f"{i}.txt").read_text(), a.casefold) for i in gold_ids}

    systems: dict[str, dict[str, str]] = {"embedded": {}}
    for p in map(json.loads, open(a.pages_file)):
        if p["page_id"] in gold:
            systems["embedded"][p["page_id"]] = p["embedded_text"]
    for mdir in sorted(Path(a.results).iterdir()):
        if mdir.is_dir():
            systems[mdir.name] = {}
            for f in mdir.glob("*.jsonl"):
                for r in map(json.loads, f.open()):
                    if r["page_id"] in gold:
                        systems[mdir.name][r["page_id"]] = r["text"]

    rows, summary = [], []
    for name, out in systems.items():
        ce = cn = we = wn = missing = 0
        for pid, ref in gold.items():
            if pid not in out:
                missing += 1
                continue
            hyp = normalise(out[pid], a.casefold)
            c, w = Levenshtein.distance(ref, hyp), Levenshtein.distance(ref.split(), hyp.split())
            ce, cn, we, wn = ce + c, cn + len(ref), we + w, wn + len(ref.split())
            rows.append(dict(system=name, page_id=pid, cer=round(c / max(1, len(ref)), 4),
                             wer=round(w / max(1, len(ref.split())), 4), ref_chars=len(ref)))
        summary.append((name, len(gold) - missing, missing, ce / cn if cn else float("nan"),
                        we / wn if wn else float("nan")))

    print(f"{'system':16s} {'pages':>5s} {'missing':>7s} {'CER':>7s} {'WER':>7s}")
    for name, n, miss, cer, wer in sorted(summary, key=lambda s: (s[3] != s[3], s[3])):
        print(f"{name:16s} {n:5d} {miss:7d} {cer:7.3f} {wer:7.3f}")
    out_csv = Path(a.results) / "eval_pages.csv"
    with out_csv.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["system", "page_id", "cer", "wer", "ref_chars"])
        w.writeheader()
        w.writerows(rows)
    print(f"per-page scores -> {out_csv}")


if __name__ == "__main__":
    main()
