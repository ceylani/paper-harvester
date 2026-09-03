"""Filesystem safety and filename sanitization utilities."""

import re
import unicodedata


def sanitize_filename(name: str, max_length: int = 40, fallback: str = "document") -> str:
    """Sanitize a raw string, URL, or path into a clean, filesystem-safe filename."""
    if not name or not name.strip():
        return fallback

    # Strip query params or hash fragments if present
    raw = name.split("?")[0].split("#")[0]

    # If it's a URL or path, isolate the final component
    raw = raw.rstrip("/\\")
    if "/" in raw or "\\" in raw:
        raw = re.split(r"[/\\]", raw)[-1]

    # Strip standard document extension
    if raw.lower().endswith(".pdf"):
        raw = raw[:-4]

    normalized = unicodedata.normalize("NFKD", raw)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    # Replace invalid characters with underscore
    clean = re.sub(r'[\\/*?:"<>|]+', "_", ascii_text)
    clean = re.sub(r"[\s\-_]+", "_", clean).strip("._")

    if not clean:
        return fallback

    if len(clean) > max_length:
        clean = clean[:max_length].rstrip("._")

    return clean or fallback
