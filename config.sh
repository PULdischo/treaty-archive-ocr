# Shared settings, read by setup_env.sh, download_models.sh and slurm/ocr.slurm.
#
# Everything large goes in your scratch folder, never /home (which is small).
# On Della that is /scratch/gpfs/<ResearchGroup>/<NetID>; `checkquota` shows it.
# setup_scratch.sh finds it and saves it in .scratch_path. You can also set
# SCRATCH_DIR yourself before running a script.
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$SCRATCH_DIR" ] && [ -f "$_here/.scratch_path" ]; then
  SCRATCH_DIR="$(cat "$_here/.scratch_path")"
fi
if [ -z "$SCRATCH_DIR" ]; then
  echo "ERROR: scratch folder not set. Run first: bash setup_scratch.sh" >&2
  return 1 2>/dev/null || exit 1
fi
export SCRATCH_DIR

# Conda environment for this project.
export ENV_PREFIX="${ENV_PREFIX:-$SCRATCH_DIR/envs/treaty-ocr}"

# Hugging Face model weights (each model is 7-18 GB). Uses HF_HOME from
# ~/.bashrc if setup_scratch.sh (or you) set it there, otherwise scratch.
export HF_HOME="${HF_HOME:-$SCRATCH_DIR/.cache/huggingface}"

# Conda and pip download caches, also off /home.
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$SCRATCH_DIR/.cache/conda-pkgs}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$SCRATCH_DIR/.cache/pip}"

# Temporary files for GPU jobs (local /tmp on Della nodes is small and shared),
# and compiled-kernel caches reused across GPU jobs.
export TMP_ROOT="${TMP_ROOT:-$SCRATCH_DIR/tmp}"
export CACHE_ROOT="${CACHE_ROOT:-$SCRATCH_DIR/.cache}"

# Della's Anaconda module.
ANACONDA_MODULE="${ANACONDA_MODULE:-anaconda3/2025.12}"

activate_env() {
  module purge
  module load "$ANACONDA_MODULE"
  conda activate "$ENV_PREFIX"
}

# Stop early if a large-file location points into /home.
for _v in ENV_PREFIX HF_HOME CONDA_PKGS_DIRS; do
  case "$(readlink -f "${!_v}" 2>/dev/null || echo "${!_v}")" in /home/*)
    echo "ERROR: $_v=${!_v} is in /home, which is too small. Run setup_scratch.sh or fix ~/.bashrc." >&2
    return 1 2>/dev/null || exit 1 ;;
  esac
done
