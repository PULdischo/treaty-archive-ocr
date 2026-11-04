#!/bin/bash
# One-time account setup: keep big files (conda envs, model weights, caches) on
# /scratch instead of /home. Follows Princeton Research Computing's advice:
#   https://researchcomputing.princeton.edu/support/knowledge-base/checkquota  ("large Conda environments", ".cache Folder")
#   https://researchcomputing.princeton.edu/support/knowledge-base/hugging-face ("Tips for Working with HF")
#
# Run once, on a Della login node, BEFORE setup_env.sh:
#
#     bash setup_scratch.sh                                   # finds your scratch folder
#     bash setup_scratch.sh /scratch/gpfs/<ResearchGroup>/<NetID>   # or give it explicitly
#
# What it does (it asks before changing anything):
#   1. Finds your scratch folder (on Della: /scratch/gpfs/<ResearchGroup>/<NetID>;
#      `checkquota` lists it) and saves it in .scratch_path for the other scripts.
#   2. Moves ~/.conda and ~/.cache to scratch and leaves symbolic links in their
#      place (rsync, then delete, then link), exactly as Research Computing describes.
#      Existing conda environments keep working.
#   3. Adds  export HF_HOME=<scratch>/.cache/huggingface/  to ~/.bashrc so Hugging
#      Face downloads go to scratch in every session, not only in our scripts.
#   4. Runs `conda clean --all` to delete old package downloads.
# Safe to run again: steps already done are skipped.
set -eo pipefail
cd "$(dirname "$0")"
YES=0
[ "$1" = "--yes" ] && { YES=1; shift; }

ask() {  # ask "question" -> returns 0 for yes
  [ $YES = 1 ] && return 0
  read -r -p "$1 [y/N] " a
  [[ "$a" =~ ^[Yy] ]]
}

# ---- 1. find the scratch folder -------------------------------------------
SCRATCH="$1"
if [ -z "$SCRATCH" ]; then
  mapfile -t found < <(ls -d /scratch/gpfs/*/"$USER" /scratch/gpfs/"$USER" 2>/dev/null || true)
  if [ ${#found[@]} -eq 1 ]; then
    SCRATCH="${found[0]}"
  else
    echo "Could not pick your scratch folder automatically (found: ${found[*]:-none})."
    echo "Run 'checkquota' and look for the 'Della scratch GPFS fileset' line, then:"
    echo "    bash setup_scratch.sh /scratch/gpfs/<ResearchGroup>/<YourNetID>"
    exit 1
  fi
fi
SCRATCH="${SCRATCH%/}"
[ -d "$SCRATCH" ] && [ -w "$SCRATCH" ] || { echo "ERROR: $SCRATCH does not exist or is not writable."; exit 1; }
echo "Scratch folder: $SCRATCH"
echo "$SCRATCH" > .scratch_path
echo "  saved to $(pwd)/.scratch_path (read by config.sh)"

# ---- 2. move ~/.conda and ~/.cache to scratch -------------------------------
move_to_scratch() {  # $1 = name under $HOME, e.g. .conda
  local name="$1" src="$HOME/$1" dst="$SCRATCH/$1"
  if [ -L "$src" ]; then
    echo "~/$name is already a link to $(readlink "$src") - skipping"
    return
  fi
  if [ ! -e "$src" ]; then
    mkdir -p "$dst"; ln -s "$dst" "$src"
    echo "~/$name did not exist; created it on scratch and linked it"
    return
  fi
  echo "~/$name is $(du -sh "$src" 2>/dev/null | cut -f1) in /home."
  if ask "Move ~/$name to $dst and leave a link in its place?"; then
    rsync -au "$src" "$SCRATCH/"
    rm -rf "$src"
    ln -s "$dst" "$src"
    echo "  moved; ~/$name -> $dst"
  else
    echo "  left in place"
  fi
}
move_to_scratch .conda
move_to_scratch .cache

# ---- 3. HF_HOME in ~/.bashrc -----------------------------------------------
HF_LINE="export HF_HOME=$SCRATCH/.cache/huggingface/"
if grep -qs "^export HF_HOME=" "$HOME/.bashrc"; then
  echo "~/.bashrc already sets HF_HOME: $(grep '^export HF_HOME=' "$HOME/.bashrc" | tail -1)"
  echo "  (leave it if it points to scratch; otherwise edit it to: $HF_LINE)"
elif ask "Add '$HF_LINE' to ~/.bashrc?"; then
  printf '\n# Hugging Face cache on scratch (added by setup_scratch.sh)\n%s\n' "$HF_LINE" >> "$HOME/.bashrc"
  echo "  added; log out and back in (or run: source ~/.bashrc) for it to take effect"
fi
mkdir -p "$SCRATCH/.cache/huggingface"

# ---- 4. clear old conda package downloads ----------------------------------
if ask "Run 'conda clean --all' to delete cached package downloads?"; then
  source config.sh
  module purge; module load "$ANACONDA_MODULE"
  conda clean --all -y
fi

echo
echo "Done. Check your space with:  checkquota"
echo "Next:  bash setup_env.sh   then   bash download_models.sh"
