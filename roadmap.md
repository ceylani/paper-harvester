# Roadmap

## Current Version (v0.1)
- Parallel academic paper downloader (arXiv, DOIs, and direct PDF links).
- Two-column layout-aware text extraction to Markdown via PyMuPDF4LLM.
- 10 citation standards (BibTeX, APA, IEEE, MLA, Chicago, Harvard, Vancouver, ISNAD 2, RIS, Plain Web).
- Bilingual interactive CLI wizard (English / Turkish) and CLI flags.
- Single file or split directory compilation.

## Version 0.2 (Planned: OCR Support)
The primary milestone for v0.2 is adding local OCR support for scanned and legacy papers that lack selectable digital text.

- **Local iGPU/NPU OCR**: Run lightweight OCR models via ONNX Runtime without requiring dedicated Nvidia GPUs. Works on integrated graphics (AMD Radeon, Intel Arc, Apple Silicon).
- **Optional Installation**: Keep the core lightweight. Users who need OCR will install an optional bundle:
  ```bash
  pip install paper-harvester[ocr]
  ```
- **Automatic Fallback**: If a paper contains scanned images instead of text, PaperHarvester will automatically switch to the OCR engine.

## Future Ideas (v0.3+)
- Export to vector databases for RAG workflows.
- Direct export to Zotero / Mendeley libraries.
