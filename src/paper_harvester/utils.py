"""Filesystem safety and filename sanitization utilities."""

import re
import unicodedata


def sanitize_filename(name: str, max_length: int = 40, fallback: str = "document") -> str:
    """Sanitize a raw string into a clean, filesystem-safe filename."""
    if not name:
        return fallback

    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    clean = re.sub(r'[\\/*?:"<>|]', "", ascii_text)
    clean = re.sub(r"[\s\-_]+", "_", clean).strip("._")

    if not clean:
        return fallback

    if len(clean) > max_length:
        clean = clean[:max_length].rstrip("._")

    return clean or fallback
