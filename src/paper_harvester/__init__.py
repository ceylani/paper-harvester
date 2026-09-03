"""PaperHarvester - Layout-Aware Academic Paper Harvester & Dossier Compiler."""

__version__ = "0.1.0b1"

from .core import (
    PaperHarvester,
    extract_academic_links,
    resolve_pdf_url,
    download_pdf,
    extract_markdown_from_pdf,
)
from .citations import (
    PaperMetadata,
    fetch_arxiv_metadata,
    generate_10_citations,
)

__all__ = [
    "PaperHarvester",
    "extract_academic_links",
    "resolve_pdf_url",
    "download_pdf",
    "extract_markdown_from_pdf",
    "PaperMetadata",
    "fetch_arxiv_metadata",
    "generate_10_citations",
    "__version__",
]
