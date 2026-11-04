#!/bin/bash
# Download OCR model weights. Run on a login or vis node (needs the internet);
# GPU compute nodes cannot download anything.
#
#     bash download_models.sh                 # all models listed in ocr/models.py
#     bash download_models.sh qwen3vl-8b      # just one (use the short names)
#
# Each model is 7-18 GB (about 50 GB for all four). They go into the Hugging
# Face cache in your scratch folder ($HF_HOME, set by setup_scratch.sh /
# config.sh), never /home. Already-downloaded files are skipped, so re-running
# also repairs an incomplete download.
set -eo pipefail
cd "$(dirname "$0")"
source config.sh
activate_env
mkdir -p "$HF_HOME"
echo "Downloading to: $HF_HOME  (resolves to $(readlink -f "$HF_HOME"))"
echo "Free space there: $(df -h --output=avail "$HF_HOME" | tail -1 | tr -d ' ')  (your quota: run checkquota)"

KEYS="$*"
[ -z "$KEYS" ] && KEYS=$(python -c "import sys; sys.path.insert(0,'ocr'); from models import MODELS; print(' '.join(MODELS))")

for key in $KEYS; do
  repo=$(python -c "import sys; sys.path.insert(0,'ocr'); from models import MODELS; print(MODELS['$key']['repo'])")
  echo "== $key ($repo)"
  for try in 1 2 3; do
    if hf download "$repo" > /dev/null; then echo "   ok"; break; fi
    echo "   retry $try"; [ $try = 3 ] && { echo "   FAILED $repo"; exit 1; }
  done
done
echo
echo "Models now in the cache:"
# (weights are links into a shared blobs folder, so follow links when measuring)
for d in "$HF_HOME"/hub/models--*; do
  printf "  %-8s %s\n" "$(du -shL --apparent-size "$d/snapshots" 2>/dev/null | cut -f1)" "$(basename "$d" | sed 's/^models--//; s/--/\//')"
done
echo "  total cache: $(du -sh --apparent-size "$HF_HOME" 2>/dev/null | cut -f1)"
