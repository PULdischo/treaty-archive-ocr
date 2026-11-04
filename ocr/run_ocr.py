#!/usr/bin/env python3
"""Step 2: OCR every page in data/pages.jsonl with one model, using vLLM on a GPU.

Run inside a Slurm job (see slurm/ocr.slurm), not on a login node.

    python ocr/run_ocr.py --model qwen3vl-8b
    python ocr/run_ocr.py --model olmocr2-7b --limit 25          # quick test
    python ocr/run_ocr.py --model qwen3vl-8b --shard 2 --num-shards 8   # one piece of a job array

Writes results/<model>/shard_<k>.jsonl, one row per page:
    page_id, model, repo, raw (model output), text (cleaned), finish_reason, n_tokens, seconds

Resumable: pages already present in any results/<model>/*.jsonl are skipped,
so a job that hits its time limit can simply be resubmitted. A page that fails
(e.g. an unreadable image) is saved with finish_reason "error" and an "error"
message instead of stopping the job; delete those rows to retry them.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import MODELS  # noqa: E402


def local_snapshot(repo: str) -> str:
    """Path of the downloaded model. Compute nodes have no internet, so never download here."""
    from huggingface_hub import snapshot_download
    try:
        path = snapshot_download(repo, local_files_only=True)
    except Exception:
        sys.exit(f"ERROR: {repo} is not downloaded. On a login node run: bash download_models.sh")
    # A half-finished download, or a cache that was partly cleaned up, leaves
    # weight shards missing; catch that now rather than after the GPU loads.
    index = Path(path) / "model.safetensors.index.json"
    if index.exists():
        shards = set(json.loads(index.read_text())["weight_map"].values())
        missing = [s for s in shards if not (Path(path) / s).exists()]
        if missing:
            sys.exit(f"ERROR: {repo} is missing {len(missing)} weight files. Re-run: bash download_models.sh")
    return path


def image_uri(path: str, max_long_side: int | None) -> str:
    img = Image.open(path).convert("RGB")
    if max_long_side and max(img.size) > max_long_side:
        img.thumbnail((max_long_side, max_long_side), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def build_messages(cfg: dict, image_path: str) -> list[dict]:
    img = {"type": "image_url", "image_url": {"url": image_uri(image_path, cfg["max_long_side"])}}
    txt = {"type": "text", "text": cfg["prompt"]}
    msgs = []
    if cfg.get("system"):
        msgs.append({"role": "system", "content": cfg["system"]})
    msgs.append({"role": "user", "content": [txt, img] if cfg["text_first"] else [img, txt]})
    return msgs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--pages", default="data/pages.jsonl")
    ap.add_argument("--results", default="results")
    ap.add_argument("--only", help="text file of page_ids to process (e.g. gold/pages.txt)")
    ap.add_argument("--limit", type=int, default=0, help="process at most N pages (testing)")
    ap.add_argument("--batch-size", type=int, default=64, help="pages per vLLM call; results saved after each")
    ap.add_argument("--shard", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_ID", 0)))
    ap.add_argument("--num-shards", type=int, default=int(os.environ.get("NUM_SHARDS", 1)))
    ap.add_argument("--gpu-mem", type=float, default=0.90)
    a = ap.parse_args()

    cfg = MODELS[a.model]
    pages = [json.loads(l) for l in open(a.pages) if l.strip()]
    if a.only:
        keep = {l.strip() for l in open(a.only) if l.strip()}
        pages = [p for p in pages if p["page_id"] in keep]
    pages = [p for i, p in enumerate(pages) if i % a.num_shards == a.shard]

    out_dir = Path(a.results) / a.model
    out_dir.mkdir(parents=True, exist_ok=True)
    done = set()
    for f in out_dir.glob("*.jsonl"):
        done |= {json.loads(l)["page_id"] for l in f.open() if l.strip()}
    todo = [p for p in pages if p["page_id"] not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{a.model}: {len(pages)} pages in shard {a.shard}/{a.num_shards}, {len(todo)} to do", flush=True)
    if not todo:
        return

    from vllm import LLM, SamplingParams  # imported late so --help works without a GPU

    n_gpu = max(1, len([d for d in os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",") if d]))
    llm = LLM(
        model=local_snapshot(cfg["repo"]),
        trust_remote_code=True,
        max_model_len=cfg["max_model_len"],
        gpu_memory_utilization=a.gpu_mem,
        tensor_parallel_size=n_gpu,
        limit_mm_per_prompt={"image": 1},
    )
    sp = SamplingParams(temperature=0.0, max_tokens=cfg["max_tokens"])

    out_path = out_dir / f"shard_{a.shard:03d}.jsonl"
    t_all = time.time()
    with out_path.open("a") as out:
        for start in range(0, len(todo), a.batch_size):
            batch = todo[start:start + a.batch_size]
            t0 = time.time()
            try:
                convs = [build_messages(cfg, p["image"]) for p in batch]
                pairs = list(zip(batch, llm.chat(convs, sp, use_tqdm=False)))
            except Exception as exc:
                # One bad page (unreadable image, prompt longer than max_model_len...)
                # fails the whole call. Redo this batch one page at a time so only
                # the bad page is lost; it is recorded with finish_reason "error".
                print(f"  batch failed ({exc}); retrying page by page", flush=True)
                pairs = []
                for p in batch:
                    try:
                        pairs.append((p, llm.chat([build_messages(cfg, p["image"])], sp, use_tqdm=False)[0]))
                    except Exception as exc1:
                        pairs.append((p, exc1))
            sec = (time.time() - t0) / len(batch)
            for p, r in pairs:
                if isinstance(r, Exception):
                    row = dict(page_id=p["page_id"], model=a.model, repo=cfg["repo"], raw="", text="",
                               finish_reason="error", error=str(r)[:500], n_tokens=0, seconds=round(sec, 3))
                    print(f"  ERROR {p['page_id']}: {str(r)[:200]}", flush=True)
                else:
                    o = r.outputs[0]
                    row = dict(page_id=p["page_id"], model=a.model, repo=cfg["repo"], raw=o.text,
                               text=cfg["clean"](o.text), finish_reason=o.finish_reason,
                               n_tokens=len(o.token_ids), seconds=round(sec, 3))
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            n = start + len(batch)
            rate = n / (time.time() - t_all)
            print(f"  {n}/{len(todo)} pages  ({rate:.2f} pages/s)", flush=True)
    print(f"done -> {out_path}")


if __name__ == "__main__":
    main()
