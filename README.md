# OCR for presidential-library treaty records on Della

This folder turns scanned archival documents into searchable text on Princeton's
Della cluster. It does two things:

1. **Finds records.** It finds likely relevant records in the National Archives
   Catalog (Carter → Obama libraries). You edit the list, and the scans you keep
   are downloaded.
2. **Runs OCR.** It runs open vision-language models (VLMs) on the scans, then
   measures their accuracy against pages you have corrected by hand. It exports
   the text as Markdown and CSV.

`PLAN.md` describes the wider project plan, including the analysis steps after
OCR. `lit_review.md` is the literature review, with a Princeton library
call number or online link for every source.

```
setup_scratch.sh       one-time: keep conda, caches and models on /scratch (not /home)
config.sh              settings: where the conda env and model files live
setup_env.sh           one-time: build the conda environment
download_models.sh     one-time: download model weights
nara/
  index/               compact copy of the NARA Catalog for the 6 presidential libraries
  search_terms.csv     search terms and weights  (edit me)
  find_candidates.py   search the index -> nara/candidates.csv
  candidates.csv       the candidate list         (edit me: keep = y / n)
  download.py          download scans for kept rows -> data/nara/<naid>/
ocr/
  prepare.py           PDFs/images -> one PNG per page + data/pages.jsonl
  run_ocr.py           OCR with one model (GPU; run through Slurm)
  models.py            the models and their prompts
  make_gold.py         pick pages for hand correction
  evaluate.py          accuracy (CER/WER) of each model against the gold pages
  export.py            Markdown per document + CSV per page
slurm/ocr.slurm        the GPU job script
data/pdfs/             put your own PDFs here (the Panama Canal sample is already there)
data/pages/            page images made by prepare.py          (not in git; rebuild with prepare.py)
results/<model>/       OCR output, one JSONL row per page        (not in git; see .gitignore)
PLAN.md                project plan;   lit_review.md   literature review
```

---

## 1. One-time setup

Log in to a Della login node. Use the GPU login node, because it has internet
access and the same GPU software as the compute nodes:

```bash
ssh <netid>@della-gpu.princeton.edu
```

Copy this folder into your **scratch** folder and go into it. On Della, scratch
is `/scratch/gpfs/<ResearchGroup>/<NetID>`; `checkquota` lists it on the
"Della scratch GPFS fileset" line.

```bash
checkquota
cd /scratch/gpfs/<ResearchGroup>/<NetID>/sun-shen
```

**Keep big files off `/home`.** Your `/home` quota is small (10–50 GB). The
conda env takes about 9 GB and the models take about 50 GB. Run this once:

```bash
bash setup_scratch.sh        # or: bash setup_scratch.sh /scratch/gpfs/<ResearchGroup>/<NetID>
```

It follows Research Computing's
[Checkquota](https://researchcomputing.princeton.edu/support/knowledge-base/checkquota)
and [Hugging Face](https://researchcomputing.princeton.edu/support/knowledge-base/hugging-face)
guides, and asks before each change:

- It moves `~/.conda` and `~/.cache` to scratch and leaves symbolic links in
  their place. Existing conda environments keep working.
- It adds `export HF_HOME=<scratch>/.cache/huggingface/` to `~/.bashrc`, so
  Hugging Face downloads go to scratch in every session.
- It runs `conda clean --all` to delete old package downloads.
- It saves your scratch path in `.scratch_path`, which all the other scripts
  read.

Then **log out and back in**, so the new `HF_HOME` takes effect. Check it with
`echo $HF_HOME`. The scripts stop with an error if anything would be written
to `/home`.

Build the environment, which takes about 10–15 minutes:

```bash
bash setup_env.sh
```

Download the models into the Hugging Face cache on scratch. There are four,
7–17 GB each, so this takes a while; the script prints where they are going
and how much space is free. They are public, so you don't need a Hugging Face
account or token. Compute nodes have no internet, so this must run on
the login node. Use `tmux` so it survives a dropped connection:

```bash
bash download_models.sh               # all four
bash download_models.sh qwen3vl-8b    # or just one
```

To use the Python scripts interactively, activate the env first:

```bash
source config.sh && activate_env
```

---

## 2. Choose records from the National Archives Catalog (optional)

https://www.archives.gov/developer/national-archives-catalog-dataset

Skip this section if you already have your PDFs from the library websites.
In that case, put them in `data/pdfs/` and go to section 3.

```bash
source config.sh && activate_env
python nara/find_candidates.py          # ~2 minutes -> nara/candidates.csv
```

Open `nara/candidates.csv` in Excel. Each row is a series, a folder
("fileUnit") or a single item that matched the search terms.

- **Set `keep` to `n`, or delete the row,** for anything you don't want.
  `keep` starts as `y` for textual records and `n` for photographs, video and
  social-media posts.
- `agreements`, `process` and `generic` show which terms matched. `score` is
  the sum of their weights. Sort or filter on these columns.
- `n_files` is the number of scanned files. `0` means the catalog describes the
  folder but has no scan, so you would need to request it from the library or
  check the library's own website.
- `catalog_url` opens the record on catalog.archives.gov.
- Use `notes` for your own notes; the scripts ignore it.

To change what is searched, edit `nara/search_terms.csv` and run the script
again. Each row has a label, a kind (`agreement`, `process`, `generic`, or
`exclude` with a negative weight), a weight, case sensitivity, and a
[regular expression](https://docs.python.org/3/howto/regex.html).
**Re-running overwrites `candidates.csv`,** so save your edited copy under
another name first. Then use `--csv` below.

Download the scans for the rows you kept. This needs the internet, so run it on
the login node, not in a Slurm job:

```bash
python nara/download.py --dry-run                  # how many files?
python nara/download.py                            # -> data/nara/<naid>/0001.jpg ...
python nara/download.py --csv my_candidates.csv    # if you saved your edits elsewhere
```

Each record's folder also gets a `record.json` with its catalog metadata, for
citation.

**Coverage warning:** the libraries have digitized very different amounts in the
catalog. Clinton and Obama have many scans; Carter, Reagan and both Bushes have
few. Many digitized folders exist only on the libraries' own websites, like the
Panama Canal sample. The candidate list is still useful there as a finding aid.

---

## 3. Prepare pages

```bash
python ocr/prepare.py data/pdfs        # your own PDFs
python ocr/prepare.py data/nara        # catalog downloads
```

This renders every page to `data/pages/` at 150 dpi and adds it to
`data/pages.jsonl`. Each PDF becomes one document. A folder of page images
(e.g. `data/nara/<naid>/0001.jpg, 0002.jpg …`) becomes one document named
`<naid>`; a catalog PDF becomes `<naid>_0001`. If a PDF already has a text layer (for example
the library's Acrobat OCR), it is saved as `embedded_text` and used as a
baseline. Re-running only adds new pages.

---

## 4. Pick the OCR model: test on a gold set first

Which model works best depends on the documents: carbon copies, handwriting,
stamps. Measure it on your own pages before processing everything.

**a. Choose about 25 pages and correct them by hand:**

```bash
python ocr/make_gold.py --sample 25
```

This writes `gold/pages.txt` and one `gold/<page_id>.txt` per page. Each file
starts with the PDF's existing text layer, which is noisy. `gold/pages.tsv`
lists the image for each page. Open each image next to its text file and edit
the text until it matches the page exactly:

- Keep the original spelling and typos. Don't fix them.
- Include handwritten notes, initials, stamps and classification markings,
  wherever they appear on the page.
- Line breaks don't matter; the scorer ignores them.

To choose particular pages instead (e.g. hard ones with handwriting), use
`--pages <page_id> <page_id> ...`. Pick a mix: clean typescript, faint carbons,
handwriting, stamps.

**b. Run each model on the gold pages.** If you received this folder as a copy
that already includes `results/` with the Panama sample's output, and your gold
pages come from that sample, you can skip this step. Otherwise:

```bash
for m in qwen3vl-8b olmocr2-7b nanonets2-3b chandra2; do
  sbatch --qos=gpu-test --time=00:45:00 --export=ALL,MODEL=$m,OCR_ARGS="--only gold/pages.txt" slurm/ocr.slurm
done
```

`--qos=gpu-test` jobs usually start within minutes. They are limited to about
an hour, which is plenty for 25 pages.

**c. Compare:**

```bash
python ocr/evaluate.py
```

```
system           pages missing     CER     WER
qwen3vl-8b          25       0   0.0xx   0.0xx
...
embedded            25       0   0.xxx   0.xxx
```

CER is the character error rate. Lower is better: 0.02 means about 2 wrong
characters in 100. `embedded` is the library's existing OCR, the baseline to
beat. `results/eval_pages.csv` has the score for every page, so you can see
*where* each model fails.

The models (definitions and prompts are in `ocr/models.py`):

| name | model | what we saw on the Panama sample (78 pp.) and 48 NARA pages (Carter, Reagan, Bush, Clinton), before any gold set |
|---|---|---|
| `qwen3vl-8b` | Qwen/Qwen3-VL-8B-Instruct | **Suggested first choice.** Clean on typescript and faint carbons; keeps handwritten notes and stamps in place, tagged `[HANDWRITTEN: …]` / `[STAMP: …]`; no runaway output. Sometimes silently "fixes" the original (adds a missing word, corrects spelling) and misreads some handwriting. |
| `chandra2` | datalab-to/chandra-ocr-2 | **Strong second / cross-check.** Read handwriting and declassification stamps best, but doesn't mark them as handwritten and may move margin notes to the end of the page. Outputs HTML (converted to text), so it is slower per page. |
| `nanonets2-3b` | nanonets/Nanonets-OCR2-3B | Smallest and good on typescript, but twice got stuck repeating a phrase that is *not on the page* (one page in each test set). Those pages are flagged `truncated`; check or re-run them with another model. Handwriting untagged. |
| `olmocr2-7b` | allenai/olmOCR-2-7B-1025 | **Not recommended here.** By design it drops headers, stamps ("THE PRESIDENT HAS SEEN", classification) and handwritten notes, which are evidence for this project. Most faithful to original spelling, though. |

To try another Hugging Face model, add an entry to `MODELS` in `ocr/models.py`,
download it with `bash download_models.sh <name>`, and run it the same way.

---

## 5. Run OCR on everything

Submit jobs from this project folder (the one containing `config.sh`):

```bash
sbatch --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm
```

The job takes one A100 GPU for up to 2 hours. Results go to
`results/<model>/`, and finished pages are saved after every batch of 64. If a
job runs out of time, **submit the same command again**: it skips the pages
already done.

For large collections (tens of thousands of pages), split the work across
several GPUs with a job array:

```bash
sbatch --array=0-7 --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm
```

**When the regular queue is slow**, chain short jobs on the fast `gpu-test`
lane instead. Each job starts where the previous one stopped:

```bash
prev=$(sbatch --parsable --qos=gpu-test --time=01:00:00 --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm)
for i in 2 3 4 5; do
  prev=$(sbatch --parsable --dependency=afterany:$prev --qos=gpu-test --time=01:00:00 \
         --export=ALL,MODEL=qwen3vl-8b slurm/ocr.slurm)
done
```

Each hour-long job does roughly 5,000 pages, minus about 3 minutes to load the
model. Shorter jobs start sooner: ask for about 1.5× the time you expect to
need. Della is down for maintenance on the **second Tuesday of each month**
(about 6 AM–2 PM). Jobs that would overlap it wait until it's over.

A page that can't be processed (a damaged image, for example) doesn't stop the
job. It is saved with `finish_reason` = `error` and an `error` message. To
retry those pages, delete their rows from `results/<model>/*.jsonl` and
resubmit.

Check jobs with `squeue -u $USER` and read the log in `logs/ocr_<jobid>.out`.
`squeue` shows why a job is waiting (Priority, Resources, …), and `sprio -u $USER`
shows its priority. After a job finishes, `jobstats <jobid>` shows how well it
used the GPU. If you belong to more than one Slurm account, add
`--account=<account>` to `sbatch`.

**Disk space:** page images take roughly 0.3 MB each, so 100,000 pages is
about 30 GB, on top of about 50 GB of models and a 9 GB conda env. Check your
scratch usage with `checkquota`.

---

## 6. Export the text

```bash
python ocr/export.py --model qwen3vl-8b
```

- `exports/qwen3vl-8b/<document>.md` has one file per folder or PDF, with
  `## Page N` headings. Use these for reading, `grep`, or importing into NVivo,
  ATLAS.ti or MAXQDA.
- `exports/qwen3vl-8b/pages.csv` has one row per page: document, page number,
  source file and text. Use it with Excel, R, Stata or pandas.

The `flag` column says `truncated` when the model hit its output limit on a
page, which usually means it got stuck repeating a line. Check those pages
against the image.

`PLAN.md` describes the next steps: splitting folders into separate documents,
extracting dates, authors and recipients, coding passages, and the analysis.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ERROR: scratch folder not set` | Run `bash setup_scratch.sh` once (section 1). |
| `ERROR: HF_HOME=... is in /home` (or `ENV_PREFIX`) | `~/.bashrc` points the cache at `/home`. Run `setup_scratch.sh`, or fix the `export HF_HOME=` line in `~/.bashrc`, then log out and back in. |
| `ERROR: <model> is not downloaded` or `is missing N weight files` | Run `bash download_models.sh <name>` on the login node; it fills in missing files. Compute nodes have no internet. |
| `Illegal instruction (core dumped)` | CPU mismatch between nodes. Add `--constraint="intel&gpu80"` to `sbatch`. |
| Pages with `finish_reason` = `error` | See the `error` field. TIFFs and huge scans are converted by `prepare.py`, so re-run it if you added files by hand. |
| `got a MIG GPU slice` | Resubmit. Keep `--constraint=gpu80` in `slurm/ocr.slurm`; vLLM can't run on Della's partitioned GPUs. |
| `sbatch: error: invalid partition` | Don't add `--partition=gpu`. Della chooses the partition itself. |
| CUDA out of memory | Lower the batch size with `OCR_ARGS="--batch-size 16"`, or lower `max_model_len` in `ocr/models.py`. |
| `decoder prompt ... longer than the maximum model length` | Page images are too big. Re-run `prepare.py` with `--dpi 120` or `--max-side 1600`. |
| A job sits in the queue for hours | Ask for less time (`--time=01:00:00`) or use `--qos=gpu-test` for small runs. Shorter jobs start sooner. |
| Download failures | Re-run `nara/download.py`; it retries only the missing files. Failures are listed in `data/nara/_failures.txt`. |
