"""Core engine for academic link resolution, resilient parallel downloads, and layout-aware compilation."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except ImportError:
    HAS_PYMUPDF4LLM = False

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

from .utils import sanitize_filename
from .citations import (
    PaperMetadata,
    fetch_arxiv_metadata,
    generate_10_citations,
    format_citations_markdown,
)

ARXIV_ABS_PATTERN = re.compile(
    r'https?://arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)',
    re.IGNORECASE,
)
PDF_DIRECT_PATTERN = re.compile(
    r'https?://[^\s<>"\'\(\)]+?\.pdf(?:[\?#][^\s<>"\'\(\)]*)?',
    re.IGNORECASE,
)
DOI_PATTERN = re.compile(
    r'https?://(?:dx\.)?doi\.org/(10\.[0-9]{4,9}/[^\s<>"\'\(\)]+)',
    re.IGNORECASE,
)
CITATION_PDF_META_REGEX = re.compile(
    r'<meta\s+(?:name|property)=["\'](?:citation_pdf_url|bepress_citation_pdf_url)["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 (PaperHarvester/0.1)"
)


def get_current_date_str() -> str:
    """Return current date formatted as DD-MM-YYYY."""
    return datetime.now().strftime("%d-%m-%Y")


def create_resilient_session(timeout: int = 30) -> requests.Session:
    """Create a requests session with exponential backoff retries."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    return session


def extract_academic_links(raw_content: str) -> List[str]:
    """Extract distinct academic URLs from raw text or Markdown."""
    found = set()
    seen_arxiv_ids = set()

    for match in ARXIV_ABS_PATTERN.finditer(raw_content):
        arxiv_id = match.group(1)
        if arxiv_id not in seen_arxiv_ids:
            seen_arxiv_ids.add(arxiv_id)
            found.add(f"https://arxiv.org/abs/{arxiv_id}")

    for match in PDF_DIRECT_PATTERN.findall(raw_content):
        clean = match.rstrip(".,;)>]")
        arxiv_m = ARXIV_ABS_PATTERN.search(clean)
        if arxiv_m:
            arxiv_id = arxiv_m.group(1)
            if arxiv_id not in seen_arxiv_ids:
                seen_arxiv_ids.add(arxiv_id)
                found.add(f"https://arxiv.org/abs/{arxiv_id}")
        else:
            found.add(clean)

    for match in DOI_PATTERN.findall(raw_content):
        found.add(f"https://doi.org/{match.rstrip('.,;)>]')}")

    return sorted(found)


def resolve_pdf_url(raw_url: str, session: Optional[requests.Session] = None) -> str:
    """Resolve arXiv abstract, DOI, or landing page URLs into direct PDF URLs."""
    arxiv_match = ARXIV_ABS_PATTERN.search(raw_url)
    if arxiv_match:
        arxiv_id = arxiv_match.group(1)
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    clean_url = raw_url.split("?")[0].split("#")[0]
    if clean_url.lower().endswith(".pdf"):
        return raw_url

    sess = session or create_resilient_session()
    try:
        resp = sess.get(raw_url, stream=True, timeout=15, allow_redirects=True)
        content_type = resp.headers.get("content-type", "").lower()
        if "application/pdf" in content_type:
            return resp.url

        initial_html = resp.raw.read(65536).decode("utf-8", errors="ignore")
        meta_match = CITATION_PDF_META_REGEX.search(initial_html)
        if meta_match:
            pdf_link = meta_match.group(1).strip()
            return urljoin(resp.url, pdf_link)
    except Exception:
        pass

    return raw_url


def is_valid_pdf_on_disk(file_path: Path) -> bool:
    """Check whether a local file exists, is non-empty, and starts with %PDF magic bytes."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception:
        return False


def download_pdf(
    url: str,
    target_path: Path,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
    force_download: bool = False,
) -> None:
    """Download a remote PDF file, validating integrity and magic bytes (%PDF)."""
    if not force_download and is_valid_pdf_on_disk(target_path):
        return

    sess = session or create_resilient_session()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sess.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()

        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    f.write(chunk)

    with open(target_path, "rb") as f:
        header = f.read(4)

    if header != b"%PDF":
        target_path.unlink(missing_ok=True)
        raise ValueError("Downloaded file is not a valid PDF (missing %PDF magic header).")


def extract_markdown_from_pdf(pdf_path: Path) -> str:
    """Extract clean, layout-aware Markdown from a PDF using pymupdf4llm."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if HAS_PYMUPDF4LLM:
        try:
            return pymupdf4llm.to_markdown(str(pdf_path))
        except Exception:
            pass

    extracted_pages = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if text:
                extracted_pages.append(text)

    return "\n\n".join(extracted_pages).strip()


class PaperHarvester:
    """Academic Harvester and Layout-Aware Dossier Compiler."""

    def __init__(
        self,
        download_dir: Path = Path("papers"),
        output_file: Path = Path("output.md"),
        mode: str = "full",
        structure_type: str = "single",
        format_type: str = "md",
        max_workers: int = 4,
        force_download: bool = False,
        timeout: int = 30,
    ):
        self.download_dir = Path(download_dir)
        self.output_file = Path(output_file)
        self.mode = mode
        self.structure_type = structure_type  # 'single' | 'split'
        self.format_type = format_type
        self.max_workers = max_workers
        self.force_download = force_download
        self.timeout = timeout
        self.session = create_resilient_session(timeout=timeout)

    def process_file(
        self,
        input_source: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[int, str]:
        """Execute the pipeline according to selected mode, structure, and format."""
        input_path = Path(input_source)
        if not input_path.exists():
            raise FileNotFoundError(f"Source file not found: {input_path}")

        raw_text = input_path.read_text(encoding="utf-8")
        raw_links = extract_academic_links(raw_text)

        if not raw_links:
            return 0, ""

        self.download_dir.mkdir(parents=True, exist_ok=True)
        total = len(raw_links)
        date_str = get_current_date_str()

        # Step 1: Pre-resolve metadata & targets
        items_to_process = []
        for index, raw_url in enumerate(raw_links, start=1):
            arxiv_match = ARXIV_ABS_PATTERN.search(raw_url)
            arxiv_id = arxiv_match.group(1) if arxiv_match else None

            meta = fetch_arxiv_metadata(arxiv_id, timeout=self.timeout) if arxiv_id else None

            if meta and meta.authors and meta.title:
                author_slug = sanitize_filename(meta.authors[0].split()[-1], max_length=20)
                title_slug = sanitize_filename(meta.title, max_length=35)
                doc_slug = f"{title_slug}_{author_slug}_{date_str}"
            else:
                base_slug = sanitize_filename(raw_url, max_length=35, fallback=f"paper_{index}")
                doc_slug = f"{base_slug}_{date_str}"

            filename = f"{index:02d}_{doc_slug}.pdf"
            file_path = self.download_dir / filename
            resolved_pdf_url = resolve_pdf_url(raw_url, session=self.session)

            if meta is None:
                meta = PaperMetadata(
                    title=f"Academic Document {index:02d}",
                    authors=["Anonymous"],
                    year=date_str.split("-")[-1],
                    identifier=raw_url,
                    url=raw_url,
                )

            citations_10 = generate_10_citations(meta)

            items_to_process.append({
                "index": index,
                "title": meta.title,
                "authors": meta.authors,
                "year": meta.year,
                "original_url": raw_url,
                "resolved_url": resolved_pdf_url,
                "filename": filename,
                "file_path": file_path,
                "citations": citations_10,
                "text": "",
                "error": None,
            })

        # Step 2: Parallel Download Worker Pool (Clean & Thread-Safe)
        if self.mode != "compile_only":
            def download_worker(item):
                idx = item["index"]
                fname = item["filename"]
                try:
                    download_pdf(
                        item["resolved_url"],
                        item["file_path"],
                        session=self.session,
                        timeout=self.timeout,
                        force_download=self.force_download,
                    )
                    return idx, fname, None
                except Exception as exc:
                    return idx, fname, str(exc)

            completed_downloads = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_map = {executor.submit(download_worker, it): it for it in items_to_process}
                for future in as_completed(future_map):
                    completed_downloads += 1
                    idx, fname, error = future.result()
                    target_item = next(it for it in items_to_process if it["index"] == idx)
                    target_item["error"] = error
                    if progress_callback:
                        status_label = f"Downloaded ({completed_downloads}/{total}): {fname}" if not error else f"Error: {fname}"
                        progress_callback(status_label, completed_downloads, total)

        # Step 3: Sequential Layout-Aware Text Extraction
        all_texts = []
        if self.mode != "download_only":
            for index, item in enumerate(items_to_process, start=1):
                if item["error"]:
                    continue
                if progress_callback:
                    progress_callback(f"Extracting layout-aware Markdown: {item['filename']}", index, total)
                try:
                    if item["file_path"].exists():
                        item["text"] = extract_markdown_from_pdf(item["file_path"])
                        if item["text"]:
                            all_texts.append(item["text"])
                    else:
                        item["error"] = "File not found locally for compilation."
                except Exception as exc:
                    item["error"] = f"Extraction error: {exc}"

            self._compile_dossier(items_to_process, input_path.name)

        return len(items_to_process), "\n\n".join(all_texts)

    def _compile_dossier(self, results: list, source_name: str) -> None:
        """Route compilation to single file or split folder structure."""
        if self.structure_type == "split":
            self._write_split_dossier(results, source_name)
        else:
            self._write_single_file_dossier(results, source_name)

    def _write_single_file_dossier(self, results: list, source_name: str) -> None:
        """Generate single compiled document."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        if self.format_type == "json":
            serializable = [
                {k: v for k, v in it.items() if k != "file_path"} for it in results
            ]
            self.output_file.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")
        elif self.format_type == "txt":
            self._write_txt_single(results, source_name)
        else:
            self._write_markdown_single(results, source_name)

    def _write_markdown_single(self, results: list, source_name: str) -> None:
        """Write single Markdown compilation with TOC and Master Bibliography."""
        lines = [
            "# Academic Paper Synthesis & Dossier",
            "",
            f"> Source Document: `{source_name}`  ",
            f"> Total Papers: {len(results)}  ",
            f"> Compilation Engine: `pymupdf4llm` (Layout-Aware)",
            "",
            "---",
            "",
            "## Table of Contents",
            "",
        ]

        for item in results:
            idx = item["index"]
            status = "❌" if item["error"] else ("⚠️" if not item["text"] else "✅")
            lines.append(f"- [{status} Paper {idx:02d}: {item['title']}](#paper-{idx:02d})")

        lines.extend(["- [📚 Master Bibliography (Toplu Kaynakça)](#master-bibliography)", "", "---", ""])

        for item in results:
            idx = item["index"]
            lines.append(f"## Paper {idx:02d}: {item['title']}")
            lines.append(f"- **Authors**: {', '.join(item['authors'])}")
            lines.append(f"- **Original Source**: {item['original_url']}")
            lines.append(f"- **Local Archive**: `papers/{item['filename']}`")
            lines.append("")
            lines.append(format_citations_markdown(item["citations"]))
            lines.append("")

            if item["error"]:
                lines.append(f"> ❌ **Status**: {item['error']}")
            elif item["text"]:
                lines.append("### Content")
                lines.append(item["text"])
            else:
                lines.append("> ℹ️ *No selectable text could be extracted.*")

            lines.extend(["", "---", ""])

        lines.append("## Master Bibliography")
        lines.append("Complete academic citations for all compiled works in standard formats:\n")

        for item in results:
            idx = item["index"]
            c = item["citations"]
            lines.append(f"### [{idx:02d}] {item['title']}")
            lines.append(f"- **APA 7**: {c['APA 7']}")
            lines.append(f"- **IEEE**: {c['IEEE']}")
            lines.append(f"- **İSNAD 2**: {c['İSNAD 2']}")
            lines.append(f"- **MLA 9**: {c['MLA 9']}")
            lines.append(f"- **Chicago**: {c['Chicago']}")
            lines.append("```bibtex")
            lines.append(c["BibTeX"])
            lines.append("```\n")

        self.output_file.write_text("\n".join(lines), encoding="utf-8")

    def _write_split_dossier(self, results: list, source_name: str) -> None:
        """Generate split directory with individual paper files and index.md."""
        output_dir = self.output_file if self.output_file.is_dir() else self.output_file.parent / "output_dossier"
        output_dir.mkdir(parents=True, exist_ok=True)

        index_lines = [
            "# Academic Paper Dossier Index",
            "",
            f"> Source Document: `{source_name}`  ",
            f"> Total Papers: {len(results)}  ",
            "",
            "---",
            "",
            "## Table of Contents",
            "",
        ]

        for item in results:
            idx = item["index"]
            clean_title = sanitize_filename(item["title"], max_length=30)
            paper_file_name = f"{idx:02d}_{clean_title}.md"
            paper_path = output_dir / paper_file_name

            status = "❌" if item["error"] else ("⚠️" if not item["text"] else "✅")
            index_lines.append(f"- [{status} Paper {idx:02d}: {item['title']}]({paper_file_name})")

            # Write individual paper Markdown file
            paper_lines = [
                f"# {item['title']}",
                "",
                f"- **Authors**: {', '.join(item['authors'])}",
                f"- **Original Source**: {item['original_url']}",
                f"- **Local PDF**: `papers/{item['filename']}`",
                "",
                format_citations_markdown(item["citations"]),
                "",
                "---",
                "",
            ]
            if item["error"]:
                paper_lines.append(f"> ❌ **Status**: {item['error']}")
            elif item["text"]:
                paper_lines.append(item["text"])
            else:
                paper_lines.append("> ℹ️ *No selectable text could be extracted.*")

            paper_path.write_text("\n".join(paper_lines), encoding="utf-8")

        index_lines.extend(["", "---", "", "## Master Bibliography", ""])
        for item in results:
            idx = item["index"]
            c = item["citations"]
            index_lines.append(f"### [{idx:02d}] {item['title']}")
            index_lines.append(f"- **APA 7**: {c['APA 7']}")
            index_lines.append(f"- **IEEE**: {c['IEEE']}")
            index_lines.append(f"- **İSNAD 2**: {c['İSNAD 2']}")
            index_lines.append("```bibtex")
            index_lines.append(c["BibTeX"])
            index_lines.append("```\n")

        (output_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    def _write_txt_single(self, results: list, source_name: str) -> None:
        """Generate clean plain text single compilation."""
        lines = [
            "==================================================================",
            "ACADEMIC PAPER COMPILATION (PLAIN TEXT DOSSIER)",
            f"Source: {source_name} | Total Papers: {len(results)}",
            "==================================================================\n",
        ]

        for item in results:
            idx = item["index"]
            lines.append(f"[{idx:02d}] {item['title']}")
            lines.append(f"Authors: {', '.join(item['authors'])} ({item['year']})")
            lines.append(f"URL: {item['original_url']}")
            lines.append(f"APA 7: {item['citations']['APA 7']}")
            lines.append("-" * 66)

            if item["error"]:
                lines.append(f"[ERROR]: {item['error']}\n")
            else:
                lines.append(item["text"])
                lines.append("\n" + "=" * 66 + "\n")

        self.output_file.write_text("\n".join(lines), encoding="utf-8")


PDFPipeline = PaperHarvester
