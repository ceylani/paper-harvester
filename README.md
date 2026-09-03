<div align="center">

# PaperHarvester

**Academic Paper Harvester & Layout-Aware Dossier Compiler**  
Version 0.1

[![Version](https://img.shields.io/badge/version-0.1-blue.svg)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Engine](https://img.shields.io/badge/engine-PyMuPDF4LLM-orange.svg)](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
[![Citations](https://img.shields.io/badge/citations-10%20standards-purple.svg)](#citation-formats)
[![Development](https://img.shields.io/badge/methodology-Vibe%20Coding%20%7C%20Gemini%203.8%20Flash%20(High)-blueviolet.svg)](https://deepmind.google/technologies/gemini/)

A command-line tool that resolves academic links (arXiv, DOIs, direct URLs), downloads papers in parallel, preserves two-column document layouts into Markdown, and generates 10 international citation formats.

[Overview](#overview) •
[Installation](#installation) •
[Usage](#usage) •
[Citation Formats](#citation-formats) •
[Project Structure](#project-structure) •
[Roadmap](roadmap.md) •
[Development Methodology](#development-methodology) •
[License](#license)

</div>

---

## Overview

Academic papers formatted in two columns present significant extraction challenges. Basic text dump utilities interweave lines from adjacent columns, causing tables, formulas, and headings to lose their structural context.

PaperHarvester addresses this issue:
1. **Academic Resolution**: Resolves arXiv abstract URLs (`/abs/` to `/pdf/`), DOI links, and academic HTML `<meta name="citation_pdf_url">` tags into direct document targets.
2. **Layout-Aware Extraction**: Uses `pymupdf4llm` to preserve multi-column reading order, outputting clean Markdown with intact tables (`|---|`) and headers.
3. **Citation Generation**: Produces 10 standard citation formats for each paper (including BibTeX, APA 7, IEEE, and ISNAD 2) alongside a consolidated master bibliography.
4. **Resilient Network Layer**: Employs parallel downloads, exponential backoff retries, and `%PDF` magic byte validation to reject corrupted files or HTML block pages.
5. **Context Window Analytics**: Calculates token estimates for single-prompt Large Language Model workflows, noting whether the text is within a 200,000-token boundary.

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip

```bash
git clone https://github.com/ceylani/paper-harvester.git
cd paper-harvester

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Usage

PaperHarvester supports an interactive terminal wizard as well as direct command-line arguments.

### Recommended Workflow (AI-Assisted Research)

You do not need to format or extract your paper links manually:
1. Conduct a literature review on research tools like **Perplexity.ai**, **Google Scholar**, or **ChatGPT / Claude**.
2. Paste the raw output, reading list, or bibliography directly into `sources.md`.
3. Run `python main.py`. PaperHarvester automatically extracts valid URLs, deduplicates arXiv IDs, downloads papers in parallel, and compiles them into a structured dossier.

---

### Interactive Wizard (Default)
Run without flags to open the bilingual interactive selection menu:

```bash
python main.py
```

The wizard prompts you for:
- Language (English / Turkish)
- Operational mode (Full Run, Download Only, Compile Only)
- Output structure (Single unified file or split directory)
- Output format (Markdown, Plain Text, JSON)

---

### Command-Line Arguments (Automation)

Bypass the interactive menu by supplying CLI flags directly:

```bash
# Full pipeline with structured JSON output
python main.py --format json

# High-speed parallel download with 8 workers
python main.py --workers 8

# Save output as individual files inside a folder
python main.py --split

# Force re-download even if already cached locally
python main.py --force

# Archive remote papers to disk without compilation
python main.py --download-only

# Compile previously downloaded papers offline
python main.py --compile-only --format md
```

#### CLI Options Reference
```text
usage: paper-harvester [-h] [-s SOURCES] [-o OUTPUT] [-d PAPERS_DIR]
                       [-f {md,txt,json}] [--download-only] [--compile-only]
                       [--split] [-w WORKERS] [--force] [-t TIMEOUT]
                       [--no-interactive] [-v]

options:
  -h, --help            Show this help message and exit.
  -s, --sources PATH    Source file containing links (default: sources.md).
  -o, --output PATH     Output file or directory path.
  -d, --papers-dir PATH Directory for downloaded PDFs (default: papers).
  -f, --format FORMAT   Compilation format: md, txt, json.
  --download-only       Download papers without running text extraction.
  --compile-only        Compile papers from the local directory without downloading.
  --split               Save output as individual files per paper inside a folder.
  -w, --workers INT     Number of concurrent download worker threads (default: 4).
  --force               Force re-download of papers even if already present locally.
  -t, --timeout SECONDS Network timeout in seconds (default: 30).
  --no-interactive      Bypass the interactive wizard and execute with defaults.
  -v, --version         Show program's version number and exit.
```

---

## Citation Formats

For each harvested paper, metadata endpoints are queried to assemble 10 citation standards:

1. **BibTeX** — Native LaTeX reference entry (`@article{...}`).
2. **APA 7th Edition** — American Psychological Association.
3. **IEEE** — Institute of Electrical and Electronics Engineers.
4. **MLA 9th Edition** — Modern Language Association.
5. **Chicago / Turabian** — Chicago Manual of Style.
6. **Harvard** — Author-date convention.
7. **Vancouver** — International Committee of Medical Journal Editors.
8. **ISNAD 2** — Türkiye Academic Citation System (Ilahiyat & Sosyal Bilimler).
9. **RIS** — Reference manager exchange format (Zotero, EndNote, Mendeley).
10. **Plain Digital Citation** — Formatted single-line web reference.

Citations are placed in collapsible `<details>` blocks inside each paper entry and compiled into a **Master Bibliography** at the document footer.

---

## Project Structure

```text
paper-harvester/
├── papers/                      # Local archive of downloaded PDFs (auto-created)
├── src/
│   └── paper_harvester/
│       ├── __init__.py          # Package initialization (v0.1)
│       ├── citations.py         # 10-format citation generator & metadata engine
│       ├── cli.py               # Terminal wizard and argument parser
│       ├── core.py              # Download engine, resolver, and compiler
│       ├── ui.py                # Pacman progress bar & token analytics
│       └── utils.py             # Filename sanitization & path safety
├── tests/
│   ├── test_citations.py        # Citation format unit tests
│   ├── test_core.py             # Download & integrity verification tests
│   ├── test_extractor.py        # Academic link extraction tests
│   ├── test_resolver.py         # URL resolution tests
│   └── test_utils.py            # Sanitization tests
├── .editorconfig                # Indentation and encoding standards
├── .gitignore                   # Ignore rules for binaries, caches, and outputs
├── LICENSE                      # MIT Open Source License
├── main.py                      # Root entrypoint
├── pyproject.toml               # PEP 621 packaging metadata
├── requirements.txt             # Production dependencies
├── roadmap.md                   # Project roadmap (v0.2 OCR plans)
└── sources.md                   # Reference paper input list
```

---

## Roadmap

Upcoming features and hardware acceleration targets are documented in [roadmap.md](roadmap.md). The primary milestone for **v0.2** will be adding local iGPU-accelerated OCR support for scanned documents.

---

## Development Methodology

This repository was architected and implemented using **Vibe Coding** paired with the **Gemini 3.8 Flash (High)** model.

The codebase underwent structured refactor passes to maintain modularity, eliminate dead code artifacts, and establish regression boundaries for two-column academic parsing.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for complete terms.
