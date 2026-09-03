"""Academic citation generation supporting top 10 global and regional citation standards."""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import requests

ARXIV_API_URL = "https://export.arxiv.org/api/query"


class PaperMetadata:
    """Structured academic paper metadata."""

    def __init__(
        self,
        title: str,
        authors: List[str],
        year: str,
        identifier: str,
        url: str,
        journal_or_venue: str = "arXiv preprint",
    ):
        self.title = title.strip().replace("\n", " ")
        self.authors = authors if authors else ["Anonymous"]
        self.year = str(year) if year else "2026"
        self.identifier = identifier
        self.url = url
        self.journal_or_venue = journal_or_venue

    @property
    def cite_key(self) -> str:
        """Create a standard BibTeX citekey (e.g. sarkar2025vibe)."""
        first_author = self.authors[0].split()[-1].lower() if self.authors else "doc"
        first_word = re.sub(r"\W+", "", self.title.split()[0].lower()) if self.title else "paper"
        return f"{first_author}{self.year}{first_word}"


def fetch_arxiv_metadata(arxiv_id: str, timeout: int = 5) -> Optional[PaperMetadata]:
    """Fetch structured metadata from the official arXiv Atom API.

    Args:
        arxiv_id: Clean arXiv identifier (e.g. 2506.23253).
        timeout: Network timeout in seconds.

    Returns:
        PaperMetadata or None if unreachable.
    """
    clean_id = re.sub(r"v\d+$", "", arxiv_id)
    params = {"id_list": clean_id}

    try:
        resp = requests.get(ARXIV_API_URL, params=params, timeout=timeout)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is not None:
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text if title_elem is not None else f"arXiv Paper {arxiv_id}"

                published_elem = entry.find("atom:published", ns)
                year = published_elem.text[:4] if published_elem is not None else "2026"

                authors = []
                for author_elem in entry.findall("atom:author", ns):
                    name_elem = author_elem.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                return PaperMetadata(
                    title=title,
                    authors=authors,
                    year=year,
                    identifier=f"arXiv:{arxiv_id}",
                    url=f"https://arxiv.org/abs/{arxiv_id}",
                    journal_or_venue="arXiv",
                )
    except Exception:
        pass

    return None


def generate_10_citations(meta: PaperMetadata) -> Dict[str, str]:
    """Generate 10 distinct academic citation formats for a given paper.

    Standards included:
    1. BibTeX
    2. APA 7
    3. IEEE
    4. MLA 9
    5. Chicago / Turabian
    6. Harvard
    7. Vancouver
    8. ISNAD 2 (Türkiye Academic Standard)
    9. RIS (Zotero / Mendeley / EndNote)
    10. Plain Digital / Web Citation
    """
    first_author = meta.authors[0]
    author_count = len(meta.authors)

    # APA Author formatting (Last, F. M., & Last, F. M.)
    def format_apa_authors(names: List[str]) -> str:
        formatted = []
        for name in names:
            parts = name.split()
            if len(parts) > 1:
                formatted.append(f"{parts[-1]}, {parts[0][0]}.")
            else:
                formatted.append(name)
        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]}, & {formatted[1]}"
        return f"{', '.join(formatted[:-1])}, & {formatted[-1]}"

    apa_authors = format_apa_authors(meta.authors)

    # IEEE Author formatting (F. M. Last, F. M. Last)
    def format_ieee_authors(names: List[str]) -> str:
        formatted = []
        for name in names:
            parts = name.split()
            if len(parts) > 1:
                formatted.append(f"{parts[0][0]}. {parts[-1]}")
            else:
                formatted.append(name)
        if len(formatted) <= 3:
            return ", and ".join(formatted) if len(formatted) == 2 else ", ".join(formatted)
        return f"{formatted[0]} et al."

    ieee_authors = format_ieee_authors(meta.authors)

    # MLA Authors
    mla_first = meta.authors[0].split()
    mla_author_str = f"{mla_first[-1]}, {' '.join(mla_first[:-1])}" if len(mla_first) > 1 else meta.authors[0]
    if author_count == 2:
        mla_author_str += f", and {meta.authors[1]}"
    elif author_count > 2:
        mla_author_str += ", et al."

    # ISNAD 2 (Türkiye) formatting: Soyadı, Adı. "Başlık". Yayın Yeri (Yıl).
    isnad_author = mla_author_str

    # 1. BibTeX
    bibtex_authors = " and ".join(meta.authors)
    bibtex = (
        f"@article{{{meta.cite_key},\n"
        f"  author    = {{{bibtex_authors}}},\n"
        f"  title     = {{{{{meta.title}}}}},\n"
        f"  journal   = {{{meta.journal_or_venue}}},\n"
        f"  year      = {{{meta.year}}},\n"
        f"  eprint    = {{{meta.identifier}}},\n"
        f"  url       = {{{meta.url}}}\n"
        f"}}"
    )

    # 2. APA 7
    apa = f"{apa_authors} ({meta.year}). {meta.title}. {meta.journal_or_venue}. {meta.url}"

    # 3. IEEE
    ieee = f'{ieee_authors}, "{meta.title}," {meta.journal_or_venue}, {meta.year}. [Online]. Available: {meta.url}'

    # 4. MLA 9
    mla = f'{mla_author_str}. "{meta.title}." {meta.journal_or_venue}, {meta.year}, {meta.url}.'

    # 5. Chicago
    chicago = f'{mla_author_str}. "{meta.title}." {meta.journal_or_venue} ({meta.year}). {meta.url}.'

    # 6. Harvard
    harvard = f"{apa_authors} {meta.year}, '{meta.title}', {meta.journal_or_venue}, viewed 2026, <{meta.url}>."

    # 7. Vancouver
    vancouver_authors = ", ".join([f"{n.split()[-1]} {n.split()[0][0]}" if len(n.split()) > 1 else n for n in meta.authors[:6]])
    if author_count > 6:
        vancouver_authors += ", et al."
    vancouver = f"{vancouver_authors}. {meta.title}. {meta.journal_or_venue}. {meta.year}; Available from: {meta.url}"

    # 8. İSNAD 2 (Türkiye Standardı)
    isnad = f'{isnad_author}. "{meta.title}". {meta.journal_or_venue} ({meta.year}). {meta.url}'

    # 9. RIS (EndNote / Zotero)
    ris_lines = [
        "TY  - JOUR",
        f"TI  - {meta.title}",
    ]
    for author in meta.authors:
        parts = author.split()
        if len(parts) > 1:
            ris_lines.append(f"AU  - {parts[-1]}, {' '.join(parts[:-1])}")
        else:
            ris_lines.append(f"AU  - {author}")
    ris_lines.extend([
        f"PY  - {meta.year}",
        f"JO  - {meta.journal_or_venue}",
        f"UR  - {meta.url}",
        "ER  - ",
    ])
    ris = "\n".join(ris_lines)

    # 10. Plain Digital / Web Citation
    web_cite = f"{first_author} et al. ({meta.year}) — {meta.title} [{meta.url}]"

    return {
        "BibTeX": bibtex,
        "APA 7": apa,
        "IEEE": ieee,
        "MLA 9": mla,
        "Chicago": chicago,
        "Harvard": harvard,
        "Vancouver": vancouver,
        "İSNAD 2": isnad,
        "RIS": ris,
        "Plain Web": web_cite,
    }


def format_citations_markdown(citations: Dict[str, str]) -> str:
    """Format the 10 citations into a clean Markdown block."""
    lines = [
        "<details>",
        "<summary><b>📚 Academic Citations (10 Formats: BibTeX, APA, IEEE, İSNAD...)</b></summary>",
        "",
        "#### 1. BibTeX",
        "```bibtex",
        citations["BibTeX"],
        "```",
        "",
        "#### 2. APA 7th Edition",
        f"> {citations['APA 7']}",
        "",
        "#### 3. IEEE",
        f"> {citations['IEEE']}",
        "",
        "#### 4. MLA 9th Edition",
        f"> {citations['MLA 9']}",
        "",
        "#### 5. Chicago / Turabian",
        f"> {citations['Chicago']}",
        "",
        "#### 6. Harvard",
        f"> {citations['Harvard']}",
        "",
        "#### 7. Vancouver",
        f"> {citations['Vancouver']}",
        "",
        "#### 8. İSNAD 2 (Türkiye Academic Standard)",
        f"> {citations['İSNAD 2']}",
        "",
        "#### 9. RIS (EndNote / Zotero / Mendeley)",
        "```ris",
        citations["RIS"],
        "```",
        "",
        "#### 10. Plain Web Citation",
        f"> {citations['Plain Web']}",
        "",
        "</details>",
    ]
    return "\n".join(lines)
