# Plan: International agreements and domestic executive authority (1980–2017)

Status (2026-11-04): literature review done; OCR pipeline and NARA candidate list built and tested on Della (see README.md). Next step: the hand-corrected gold set, done by Sun Shen. Segmentation, coding and analysis (B3, C) are not built yet.

## The research claim, restated

When U.S. executive authority meets domestic resistance (Congress, courts,
states, interest groups), presidents can use international agreements to get
regulatory or enforcement authority they could not get at home. The archive
should show two things:

1. **Domestic implementation problems discussed during negotiation.**
2. **Officials explaining how the agreement helps** solve those problems.

The sample folder (Carter Library, Hamilton Jordan's confidential files, Panama
Canal, June–July 1977, 78 pages) already shows both elements. Examples are
"Steps to obtain congressional and public support for a treaty", target-state
lists for Senate votes, and Brzezinski replies to senators. So the material
fits the claim. Note that 1977 falls before the 1980–2017 window. Either the
window should start earlier, or Panama is a pilot case only.

---

## Workstream A — Literature survey

**Status: first pass done → [lit_review.md](lit_review.md)** (126 verified
sources, a 16-row mechanism table M1–M15 + C0, and a list of items still to
check). Main revisions to the plan below:
- **Prior work.** The gap is partly filled for single issue areas: anti-bribery
  (Brewster 2017), environment (DeSombre 2000) and trade (Nzelibe 2011).
  Position the project as generalizing and testing these across
  administrations from Carter to Obama.
- **Closest competitor.** Gawthorpe 2026 (*PSQ*, "Presidential
  Extra-Territorialization", doi:10.1111/psq.70043).
- **Coding scheme.** Code **C0, constraint only**, avoids selecting on the
  outcome. The Panama sample is mostly constraint evidence.
- **Document types and leads.** Look for State Dept **Circular 175** memos,
  which request authority to negotiate and state the legal basis. The 2024
  National Security Archive briefing book on Montreal (EBB #868) has a
  courts-as-motive example.

### A1. Questions the survey must answer
- **Q1.** What theories say international commitments change domestic
  bargaining power, and through which mechanisms?
- **Q2.** What do we know about U.S. presidents choosing treaties versus
  executive agreements, and about unilateral power in foreign affairs?
- **Q3.** What evidence is there that domestic politics and implementation are
  discussed explicitly during international negotiations?
- **Q4.** What archival or process-tracing studies have used
  presidential-library records on specific agreements? These are the method
  precedents and the direct competition.

### A2. Starting bibliography (seed set)
These are cited from memory. Check every citation before use.

**Two-level games and domestic politics of cooperation**
- Putnam 1988, "Diplomacy and Domestic Politics: The Logic of Two-Level Games",
  *IO*. Introduces win-sets and **synergistic issue linkage**: using a
  negotiation to change what is feasible at home. This is the core anchor.
- Evans, Jacobson & Putnam (eds.) 1993, *Double-Edged Diplomacy*. Case studies.
- Milner 1997, *Interests, Institutions, and Information*.
- Moravcsik 1994, "Why the European Community Strengthens the State"
  (working paper). Executives use international cooperation to **"cut slack"**
  from domestic constraints. This is the closest theoretical match to the claim.
- Schelling 1960; Fearon 1997 ("Signaling Foreign Policy Interests"). Covers
  **tying hands**.
- Vreeland 2003, *The IMF and Economic Development*. Governments invite outside
  conditions to push reforms through against domestic veto players. It is a good
  analogue from outside the U.S.
- Mansfield, Milner & Rosendorff 2002, "Why Democracies Cooperate More", *IO*.
- Dai 2007, *International Institutions and National Policies*; Simmons 2009,
  *Mobilizing for Human Rights*. Both cover how international commitments act
  inside domestic politics.

**U.S. institutions: treaties, executive agreements, presidential power**
- Martin 2000, *Democratic Commitments*; Martin 2005, "The President and
  International Commitments: Treaties as Signaling Devices", *PSQ*.
- Krutz & Peake 2009, *Treaty Politics and the Rise of Executive Agreements*.
- Caruson & Farrar-Myers 2007, "Promoting the President's Foreign Policy Agenda:
  Presidential Use of Executive Agreements as Policy Vehicles", *PRQ*.
- Hathaway 2008, "Treaties' End", *Yale LJ*; Hathaway 2009, "Presidential Power
  over International Law", *Yale LJ*.
- Bradley & Goldsmith 2018, "Presidential Control over International Law",
  *Harvard LR*. Closest legal-scholarship match: presidents use international
  law to widen their domestic authority.
- Moe & Howell 1999; Howell 2003, *Power without Persuasion*. Unilateral action.
- Auerswald & Maltzman 2003, "Policymaking through Advice and Consent", *JOP*.
  Senate reservations.

**Moving policy to the international level to escape domestic constraints**
- Baumgartner & Jones 1993, *Agendas and Instability*. Venue shopping.
- Guiraudon 2000, "European Integration and Migration Policy: Vertical
  Policy-Making as Venue Shopping", *JCMS*.
- Raustiala 2005, "Form and Substance in International Agreements", *AJIL*.

**Case literature (pilot and likely cases)**
- Panama: Moffett 1985, *The Limits of Victory*; Clymer 2008, *Drawing the Line
  at the Big Ditch*.
- NAFTA side agreements: Mayer 1998, *Interpreting NAFTA*. This is an explicit
  two-level-game account built on interviews and documents.
- Montreal Protocol (Benedick, *Ozone Diplomacy*); INF and START; Kyoto and the
  Paris Agreement (Paris as an executive agreement chosen to avoid the Senate).

### A3. Method
1. **Seed and snowball.** Start from the seed list. Pull forward and backward
   citations from OpenAlex or Semantic Scholar, mainly for Putnam 1988,
   Moravcsik 1994, Krutz & Peake 2009 and Bradley & Goldsmith 2018.
2. **Screen** titles and abstracts against Q1–Q4. Record decisions in a
   spreadsheet with columns: citation, Q tag, mechanism, empirical setting,
   data source, include/exclude.
3. **Build a mechanism table.** Extract each causal mechanism from the
   literature: cutting slack, tying hands, synergistic linkage, scapegoating,
   venue shopping, side payments, signaling.
   Record each one's observable implications **in archival documents**.
   Example: for "cutting slack", look for memos saying the treaty lets the
   agency act without new legislation.
4. **Find the gap.** We expect the literature to be strong on theory and on
   large-N treaty-versus-executive-agreement counts, but thin on direct
   archival evidence of the *intent* to use agreements to overcome domestic
   resistance. The archival corpus fills that gap.
5. **Output:** a ~10-page annotated review plus the mechanism table. The
   mechanism table becomes the **codebook in Workstream C**, so the theory
   directly drives the text analysis.

---

## Workstream B — Corpus and OCR on Della

### B1. Where the documents come from
- **Presidential library websites.** Carter, Reagan, Bush 41, Clinton, Bush 43
  and Obama all publish digitized folder PDFs. The sample PDF
  (`cos_142099_36_01-...`) is one of these, with a folder citation as its
  cover page. These folders will probably be the main source.
- **NARA Catalog (AWS open dataset).** `../nara_trainer/concept_index` already
  indexes every presidential-library collection:

  | Library | descriptions | digital objects | titles matching treaty/agreement terms |
  |---|---|---|---|
  | Carter (JC-*) | 177k | 30k | 3,563 recs / 442 objs |
  | Reagan (RR-*) | 33k | 60k | 717 / 1,285 |
  | Bush 41 (GB-*) | 223k | 64k | 4,033 / 223 |
  | Clinton (WJC-*) | 130k | 1.94M | 1,209 / 15,946 |
  | Bush 43 (GWB-*) | 51k | 48k | 688 / 675 |
  | Obama (BHO-*) | 153k | 149k | 2,268 / 2,263 |

  Clinton is heavily digitized in the catalog, mostly as FOIA PDFs that
  already have NARA OCR. Carter is mostly description-only. That makes the
  catalog **mainly a discovery tool**: find folder titles and series, then get
  the scans from the library websites where the catalog has no images.
  Reuse `harvest.py` and `select_batch.py` (DuckDB queries) and
  `download_images.py` (runs on a vis node, since compute nodes have no
  internet).
- **Editable candidate list (built).** The presidential-library slice of the
  index (56 MB) is copied into `nara/index/`, so Sun Shen can re-run searches
  without access to `nara_trainer`. The workflow:
  1. `nara/find_candidates.py` matches titles, scope notes and parent
     series/folder titles against `nara/search_terms.csv`. That file has about
     45 agreement terms, ratification/implementation terms, generic terms, and
     negative-weight exclusions such as "Treaty Room" and photographs.
  2. It writes `nara/candidates.csv` with columns `keep` / `notes` / `score`, the
     matched terms, library, NAID, level, title, series, folder, creator, date,
     textual flag, file count, NARA OCR flag and catalog URL. `keep` starts as
     "y" for textual records and "n" for photos and social media.
  3. Sun Shen edits it in Excel, deleting rows or setting `keep=n`.
  4. `nara/download.py` fetches the scans for kept rows into
     `data/nara/<naid>/` with a `record.json` for citation. Then
     `ocr/prepare.py data/nara` treats each folder as one document.

  First run: 10,111 candidates, ~4,700 with scans. Spot checks: textual
  folders are precise (e.g. "SALT II - Sen. Joseph Biden", "CFE -
  Ratification"); most of the noise was Obama photographs and Twitter posts,
  which now default to `keep=n`. Records with `n_files = 0` are described but
  not digitized, so they are a list of folders to request from the library.
- **Agreement list as the spine.** Build a table of the agreements to study
  (name, date, treaty or executive agreement, president, issue area). Use it
  to drive the folder searches. Candidate sources are the State Dept Treaties
  in Force, Krutz & Peake's data and the Congressional Research Service.

### B2. OCR pipeline (adapting `PULdischo/vlms-on-hpc`)
`main_pdf.py` from vlms-on-hpc is the starting point: vLLM offline,
PyMuPDF turns pages into images, batched `llm.chat`. Changes needed for
this corpus:
- **Della, not Adroit.** Set `--constraint=gpu80` (or `gpu40&nomig`), no
  `--partition`, `HF_HUB_OFFLINE=1`, and a check that exits on MIG GPUs.
  Download weights on `della-gpu` or a vis node. See
  `../DELLA_HPC_GUIDE.md`. The existing `ficherito-vllm` env (vLLM 0.28,
  transformers 5.18) can be used for prototyping.
- **Output per page, not per PDF.** Write one JSONL row per page with
  `{folder_id, pdf, page, model, text, acrobat_text}`. This makes jobs
  resumable and lets citations point to a page. Raise dpi to about 150; these
  are typewritten carbons with handwriting.
- **Prompt for archival features.** Keep classification markings (SECRET-GDS),
  declassification stamps (E.O. 12356, NLC numbers), handwritten marginalia and
  initials, and routing ("THRU:", "FROM:"). Tag them rather than drop them,
  because a presidential note like "I agree" is evidence.
- **Choose the model empirically.** Build a 25-page gold set from the sample
  PDF: clean typescript, smudged carbon, handwriting, stamps. Hand-correct it
  and compare 2–3 candidates by CER/WER. The researcher's HF-tested models
  come first, then e.g. olmOCR-2, Qwen3-VL-8B, dots.ocr or Nanonets-OCR2.
  Use the embedded Acrobat OCR as the baseline to beat.
- **Scale.** A 7–8B model on one A100 80GB should handle thousands of pages
  per hour. Even 100k pages is a few short jobs, so use `gpu-test`-sized
  chunks.

### B3. Post-OCR structuring (still on GPU, an LLM pass)
Folder PDFs mix many documents together, and drafts repeat. In the sample,
pages 27–30, 33–39 and 61–63 repeat earlier pages.
1. **Segment pages into documents.** Use the memo header, letterhead and date
   as boundaries.
2. **Extract metadata** with guided JSON output: date, author, recipient(s),
   document type, classification, agreement referred to.
3. **Remove near-duplicates** with MinHash. Keep the drafts linked, because
   differences between drafts can matter.
4. The result is one row per document. This document table is the unit for
   all later analysis.

---

## Workstream C — Analysis (answers the researcher's Q2)

The aim is to go beyond keyword search and LLM extraction of passages. In
rough order of rigor:

1. **Codebook-driven annotation (the core).** Codes come from the mechanism
   table in A3. Examples: *domestic obstacle* (Congress, courts, states,
   industry), *agreement as solution*, *implementation authority*,
   *ratification strategy*.
   - The researcher and an RA hand-code a stratified sample of ~200
     documents. Report intercoder reliability (Krippendorff's α).
   - An LLM then codes the full corpus with the same codebook. Each code must
     carry quoted evidence spans and page citations. Validate it against the
     hand-coded set (precision and recall per code) before using it at scale.
   - The output is measurable: for example, the share of negotiation-phase
     documents that pair a domestic obstacle with an agreement-as-solution
     argument, by agreement and administration.
2. **Process tracing per agreement.** Build dated timelines from the document
   table, covering negotiation, signature, ratification and implementation.
   Overlay the coded passages to see *when* domestic implementation becomes
   part of the negotiation argument. This matches standard process-tracing
   method (Bennett & Checkel; Beach & Pedersen).
3. **Semantic retrieval instead of keywords.** Use embeddings plus a reranker
   to find passages similar to known examples, not just keyword hits.
   Keyword-in-context concordances stay useful for transparency.
4. **Exploratory text analysis.** Topic models with covariates (STM or
   BERTopic over time), run by administration, agreement type and negotiation
   phase. Treaty versus executive agreement is the most interesting contrast.
5. **Actor networks.** Build author→recipient graphs from memo headers: who
   carries the domestic-implementation argument (White House Counsel,
   Congressional Liaison, NSC, agencies)?
6. **Visualizations.** Per-agreement timelines with code markers; code
   prevalence by phase; actor network; a small searchable static site with
   page images next to the OCR text, as vlms-on-hpc already does.

---

## Output formats

Each stage keeps a stable ID (`page_id`, `doc_id`, catalog NAID), so every
output can be traced back to an exact page and cited.

| Output | Format | For | Status |
|---|---|---|---|
| Page OCR, full record | `results/<model>/*.jsonl` (raw + cleaned text, model, finish reason) | the pipeline, re-processing | built |
| Reading copy | `exports/<model>/<doc>.md`, one file per folder with `## Page N` headings | reading, grep, NVivo/ATLAS.ti/MAXQDA import | built |
| Page table | `exports/<model>/pages.csv` | Excel, R, Stata, pandas | built |
| OCR accuracy | `results/eval_pages.csv` + CER/WER summary | choosing a model, methods section | built |
| Candidate records | `nara/candidates.csv` | selecting what to download | built |
| Document table | CSV/Parquet, one row per document after segmentation: dates, author, recipients, type, classification, agreement, page range, source folder, NAID, **ready-made archival citation** | timelines, networks, filtering | planned (B3) |
| Coded passages | CSV: doc, page, code, quoted text, coder (human/LLM), confidence | the main evidence base for the claim, reliability stats | planned (C1) |
| Searchable PDFs | original scan with an invisible text layer added | reading and searching in Acrobat or Zotero | planned (text is page-level, not word-positioned) |
| Browse site | static HTML: page image next to its text, full-text search, filter by agreement or library | sharing with collaborators and RAs | planned |
| Visualizations | timelines per agreement, code prevalence by negotiation phase, author→recipient networks | the paper | planned (C2–C6) |

---

## Phasing

| Phase | Work | Output | Status |
|---|---|---|---|
| 0 | Meet researcher; agree on agreement list and time window | case table | to do |
| 1 | Lit survey seed + snowball (A1–A3) | mechanism table, draft codebook | **done** (lit_review.md; 13 items still to check) |
| 1 | OCR bake-off on the sample PDF (B2) | model choice, CER numbers | pipeline built; all 4 models run on the 78-page sample; **gold pages not yet corrected** (Sun Shen), so no CER numbers or model choice yet |
| 2 | Catalog discovery + downloads for 2–3 pilot agreements | pilot corpus | candidate CSV + downloader **built**; Sun Shen to edit the CSV and pick pilots |
| 2 | OCR + segmentation + metadata at pilot scale (B2–B3) | document table | OCR ready; **segmentation/metadata not built** |
| 3 | Hand-code, validate LLM coding, timelines (C1–C2) | pilot findings | not started |
| 4 | Scale to the full agreement list; topic, network and visual work | paper-ready analysis | not started |

## Open questions for the researcher
- Which agreements, and how many? Should the window extend to 1977 so
  Panama can be included?
- Are the PDFs already downloaded? How many pages, and from which libraries?
- Which HF models did you test? (The screenshots weren't included.)
- Is there RA time for hand-coding, and does the researcher have their own
  Della allocation and scratch space?
