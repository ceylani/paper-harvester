"""Unit tests for core downloading, error handling, and magic byte validation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from paper_harvester.core import download_pdf


class TestCorePipeline(unittest.TestCase):
    """Test suite for downloading logic and PDF integrity boundaries."""

    def test_valid_pdf_magic_bytes_accepted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "valid.pdf"
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"%PDF-1.5 fake academic content"]
            mock_session.get.return_value.__enter__.return_value = mock_response

            download_pdf("https://example.com/paper.pdf", target, session=mock_session)
            self.assertTrue(target.exists())
            self.assertTrue(target.read_bytes().startswith(b"%PDF"))

    def test_invalid_html_payload_rejected_by_magic_bytes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "invalid.pdf"
            mock_session = MagicMock()
            mock_response = MagicMock()
            # Server returns 200 OK but body is an HTML cloudflare or error page
            mock_response.iter_content.return_value = [b"<!DOCTYPE html><html>404 Not Found</html>"]
            mock_session.get.return_value.__enter__.return_value = mock_response

            with self.assertRaises(ValueError) as ctx:
                download_pdf("https://example.com/paper.pdf", target, session=mock_session)

            self.assertIn("magic header", str(ctx.exception).lower())
            # The invalid file should be deleted from disk
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
