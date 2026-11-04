#!/bin/bash
# Create the conda environment for this project. Run ONCE, on a Della login node
# (della-gpu.princeton.edu) or vis node, because it needs the internet:
#
#     bash setup_env.sh
#
# Takes about 10-15 minutes. Settings (env location, caches) are in config.sh.
set -eo pipefail
cd "$(dirname "$0")"
source config.sh

module purge
module load "$ANACONDA_MODULE"
mkdir -p "$(dirname "$ENV_PREFIX")" "$HF_HOME" "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR" logs  # Slurm needs logs/ to exist

if [ -x "$ENV_PREFIX/bin/python" ]; then
  echo "Env already exists at $ENV_PREFIX - updating packages."
else
  echo "Creating env at $ENV_PREFIX"
  conda create -y -p "$ENV_PREFIX" python=3.12
fi

"$ENV_PREFIX/bin/pip" install --upgrade pip
"$ENV_PREFIX/bin/pip" install -r requirements.txt

echo
echo "Checking the install..."
"$ENV_PREFIX/bin/python" - <<'EOF'
import torch, vllm, transformers, pymupdf, rapidfuzz
print(f"vllm {vllm.__version__} | torch {torch.__version__} (CUDA {torch.version.cuda}) | "
      f"transformers {transformers.__version__} | pymupdf {pymupdf.__version__}")
EOF

echo
echo "Done. To use it:"
echo "    module load $ANACONDA_MODULE && conda activate $ENV_PREFIX"
echo "Next: bash download_models.sh"
