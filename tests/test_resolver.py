"""Unit tests for smart academic PDF resolution."""

import unittest
from unittest.mock import MagicMock
from paper_harvester.core import resolve_pdf_url


class TestResolvePdfUrl(unittest.TestCase):
    """Test suite for smart URL resolution."""

    def test_arxiv_abs_to_pdf_resolution(self):
        url = "https://arxiv.org/abs/2512.11922"
        resolved = resolve_pdf_url(url)
        self.assertEqual(resolved, "https://arxiv.org/pdf/2512.11922.pdf")

    def test_direct_pdf_unmodified(self):
        url = "https://example.com/papers/model.pdf"
        resolved = resolve_pdf_url(url)
        self.assertEqual(resolved, url)

    def test_html_meta_citation_pdf_tag_resolution(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://academic.oup.com/article/123"
        html_payload = """
        <html><head>
        <meta name="citation_pdf_url" content="https://academic.oup.com/article/download/123.pdf">
        </head><body>Paper Abstract</body></html>
        """
        mock_response.raw.read.return_value = html_payload.encode("utf-8")
        mock_session.get.return_value = mock_response

        resolved = resolve_pdf_url("https://academic.oup.com/article/123", session=mock_session)
        self.assertEqual(resolved, "https://academic.oup.com/article/download/123.pdf")


if __name__ == "__main__":
    unittest.main()
