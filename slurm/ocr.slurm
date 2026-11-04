#!/bin/bash
# OCR all prepared pages with one model on one GPU.
#
#   sbatch --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm
#   sbatch --export=ALL,MODEL=qwen3vl-8b,OCR_ARGS="--only gold/pages.txt" slurm/ocr.slurm
#   sbatch --array=0-7 --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm     # split over 8 GPUs
#
# Quick tests start in seconds on the test queue:
#   sbatch --qos=gpu-test --time=00:30:00 --export=ALL,MODEL=qwen3vl-8b,OCR_ARGS="--limit 20" slurm/ocr.slurm
#
# A job that runs out of time can be resubmitted unchanged; finished pages are skipped.
# Submit from the project folder (the one containing config.sh).
#SBATCH --job-name=ocr
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --constraint=gpu80
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --mail-type=end,fail
##SBATCH --account=<your-account>      # only needed if you belong to several Slurm accounts
# Do NOT add --partition=gpu: Della picks the partition itself and rejects that line.
set -eo pipefail
cd "$SLURM_SUBMIT_DIR"
source config.sh
activate_env

MODEL=${MODEL:?"set MODEL, e.g. sbatch --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm"}
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export VLLM_USE_FLASHINFER_SAMPLER=0
export NUM_SHARDS=${SLURM_ARRAY_TASK_COUNT:-1}
# Local /tmp on Della nodes is small (~110 GB, shared); keep vLLM/torch temp files on scratch.
export TMPDIR="$TMP_ROOT/$SLURM_JOB_ID"; mkdir -p "$TMPDIR"; trap 'rm -rf "$TMPDIR"' EXIT
# Compiled GPU kernels are reused by later jobs, so keep their caches out of the per-job TMPDIR.
export TORCHINDUCTOR_CACHE_DIR="$CACHE_ROOT/torchinductor" TRITON_CACHE_DIR="$CACHE_ROOT/triton"

# vLLM crashes on Della's MIG GPU slices; stop now rather than after a long wait.
if [[ "$CUDA_VISIBLE_DEVICES" == *MIG-* ]]; then
  echo "ERROR: got a MIG GPU slice ($CUDA_VISIBLE_DEVICES). Resubmit; keep --constraint=gpu80."; exit 1
fi
echo "job $SLURM_JOB_ID task ${SLURM_ARRAY_TASK_ID:-0}/$NUM_SHARDS on $SLURMD_NODENAME, model $MODEL"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

python ocr/run_ocr.py --model "$MODEL" $OCR_ARGS
