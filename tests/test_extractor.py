"""Unit tests for academic link and Arxiv identifier extraction."""

import unittest
from paper_harvester.core import extract_academic_links


class TestExtractAcademicLinks(unittest.TestCase):
    """Test suite for extracting academic paper links."""

    def test_direct_pdf_links(self):
        sample = "Here is a paper: https://example.com/deep_learning.pdf"
        links = extract_academic_links(sample)
        self.assertEqual(len(links), 1)
        self.assertIn("https://example.com/deep_learning.pdf", links)

    def test_arxiv_abstract_and_pdf_links(self):
        sample = """
        1. https://arxiv.org/abs/2512.11922
        2. https://arxiv.org/pdf/2506.23253
        3. [Vibe Coding](https://arxiv.org/abs/2510.17842)
        """
        links = extract_academic_links(sample)
        self.assertEqual(len(links), 3)
        self.assertIn("https://arxiv.org/abs/2512.11922", links)
        self.assertIn("https://arxiv.org/abs/2506.23253", links)
        self.assertIn("https://arxiv.org/abs/2510.17842", links)

    def test_doi_links(self):
        sample = "Reference DOI: https://doi.org/10.1145/3313831.3376722"
        links = extract_academic_links(sample)
        self.assertEqual(len(links), 1)
        self.assertIn("https://doi.org/10.1145/3313831.3376722", links)

    def test_duplicate_removal(self):
        sample = """
        https://arxiv.org/abs/2512.11922
        https://arxiv.org/abs/2512.11922
        https://arxiv.org/pdf/2512.11922
        """
        links = extract_academic_links(sample)
        # abs and pdf for same ID are normalized to abs representation in extractor
        self.assertEqual(len(links), 1)

    def test_empty_content(self):
        self.assertEqual(extract_academic_links("No papers here"), [])


if __name__ == "__main__":
    unittest.main()
