"""Registry of OCR models: Hugging Face repo, prompt, and how to clean the output.

To add a model, add an entry to MODELS. Prompts for the specialised OCR models
are copied from their own documentation, because those models were trained on
them and do worse with other prompts:
  - olmOCR-2:   allenai/olmocr  olmocr/prompts/prompts.py  build_no_anchoring_v4_yaml_prompt
  - Nanonets:   nanonets/Nanonets-OCR2-3B model card
  - Chandra:    datalab-to/chandra  chandra/prompts.py  OCR_PROMPT
General-purpose VLMs (Qwen3-VL) get ARCHIVAL_PROMPT, written for this project.
"""
from __future__ import annotations

import html
import re

ARCHIVAL_PROMPT = """You are transcribing one page from a U.S. presidential library archive: typewritten memos, letters, cables and reports, often carbon copies with handwritten notes and stamps.

Transcribe ALL text on the page exactly as written, in natural reading order, as plain text.
- Do not correct spelling, grammar or typos. Do not summarize, translate or comment.
- Keep paragraph breaks. Keep memo header lines (TO:, FROM:, THRU:, SUBJECT:, DATE:) on separate lines.
- Put handwritten text (notes, marginalia, signatures, initials) in [HANDWRITTEN: ...]. If it is outside the main text, say where, e.g. [HANDWRITTEN, left margin: ...].
- Put stamps and markings (classification such as SECRET or CONFIDENTIAL, DECLASSIFIED stamps, file and case numbers, date-received stamps) in [STAMP: ...].
- Write struck-through text as [STRUCK: ...].
- Write [ILLEGIBLE] for text you cannot read. Do not guess.
- If the page is blank, output only [BLANK PAGE]."""

OLMOCR_PROMPT = (
    "Attached is one page of a document that you must process. "
    "Just return the plain text representation of this document as if you were reading it naturally. Convert equations to LateX and tables to HTML.\n"
    "If there are any figures or charts, label them with the following markdown syntax ![Alt text describing the contents of the figure](page_startx_starty_width_height.png)\n"
    "Return your output as markdown, with a front matter section on top specifying values for the primary_language, is_rotation_valid, rotation_correction, is_table, and is_diagram parameters."
)

NANONETS_PROMPT = (
    "Extract the text from the above document as if you were reading it naturally. Return the tables in html format. "
    "Return the equations in LaTeX representation. If there is an image in the document and image caption is not present, "
    "add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. "
    "Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in "
    "brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using ☐ and ☑ for check boxes."
)

_CHANDRA_TAGS = ["math", "br", "i", "b", "u", "del", "sup", "sub", "table", "tr", "td", "p", "th", "div", "pre", "h1",
                 "h2", "h3", "h4", "h5", "ul", "ol", "li", "input", "a", "span", "img", "hr", "tbody", "small",
                 "caption", "strong", "thead", "big", "code", "chem"]
_CHANDRA_ATTRS = ["class", "colspan", "rowspan", "display", "checked", "type", "border", "value", "style", "href", "alt",
                  "align", "data-bbox", "data-label"]
CHANDRA_PROMPT = f"""OCR this image to HTML.

Only use these tags {_CHANDRA_TAGS}, and these attributes {_CHANDRA_ATTRS}.

Guidelines:
* Inline math: Surround math with <math>...</math> tags. Math expressions should be rendered in KaTeX-compatible LaTeX. Use display for block math.
* Tables: Use colspan and rowspan attributes to match table structure.
* Formatting: Maintain consistent formatting with the image, including spacing, indentation, subscripts/superscripts, and special characters.
* Images: Include a description of any images in the alt attribute of an <img> tag. Do not fill out the src property. Describe in detail inside the div tag. Also convert charts to high fidelity data, and convert diagrams to mermaid.
* Forms: Mark checkboxes and radio buttons properly.
* Text: join lines together properly into paragraphs using <p>...</p> tags.  Use <br> tags for line breaks within paragraphs, but only when absolutely necessary to maintain meaning.
* Chemistry: Use <chem>...</chem> tags for chemical formulas with reactive SMILES.
* Lists: Preserve indents and proper list markers.
* Use the simplest possible HTML structure that accurately represents the content of the block.
* Make sure the text is accurate and easy for a human to read and interpret.  Reading order should be correct and natural."""


# ---------------------------------------------------------------- cleaning --

def strip_front_matter(text: str) -> str:
    """olmOCR starts its answer with a YAML block between --- lines."""
    return re.sub(r"\A\s*---\n.*?\n---\n?", "", text, flags=re.DOTALL)


def html_to_text(text: str) -> str:
    """Turn simple HTML (Chandra, Nanonets tables) into plain text with line breaks."""
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|table|pre|caption)>", "\n", text)
    text = re.sub(r"(?i)</t[dh]>", "\t", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_none(text: str) -> str:
    return text.strip()


def clean_olmocr(text: str) -> str:
    return strip_front_matter(text).strip()


def clean_html(text: str) -> str:
    return html_to_text(text)


# ---------------------------------------------------------------- registry --
# key: short name used on the command line and for the results folder.
#   repo          Hugging Face model id
#   prompt        text prompt sent with each page image
#   text_first    put the prompt before the image (olmOCR's convention)
#   system        optional system message
#   max_long_side resize page images so the longest side is at most this (None = keep rendered size)
#   max_tokens    generation limit per page
#   max_model_len vLLM context length (image tokens + prompt + output)
#   clean         function turning the raw model output into plain text

MODELS: dict[str, dict] = {
    "qwen3vl-8b": dict(
        repo="Qwen/Qwen3-VL-8B-Instruct", prompt=ARCHIVAL_PROMPT, text_first=False, system=None,
        max_long_side=None, max_tokens=4096, max_model_len=16384, clean=clean_none),
    "olmocr2-7b": dict(
        repo="allenai/olmOCR-2-7B-1025", prompt=OLMOCR_PROMPT, text_first=True, system=None,
        max_long_side=1288, max_tokens=4096, max_model_len=16384, clean=clean_olmocr),
    "nanonets2-3b": dict(
        repo="nanonets/Nanonets-OCR2-3B", prompt=NANONETS_PROMPT, text_first=False,
        system="You are a helpful assistant.",
        max_long_side=None, max_tokens=4096, max_model_len=16384, clean=clean_html),
    "chandra2": dict(
        repo="datalab-to/chandra-ocr-2", prompt=CHANDRA_PROMPT, text_first=False, system=None,
        max_long_side=None, max_tokens=8192, max_model_len=20480, clean=clean_html),
}


if __name__ == "__main__":
    for k, v in MODELS.items():
        print(f"{k:14s} {v['repo']}")
