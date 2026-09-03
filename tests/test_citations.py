"""Unit tests for the 10 academic citation standards."""

import unittest
from paper_harvester.citations import PaperMetadata, generate_10_citations, format_citations_markdown


class TestCitationsEngine(unittest.TestCase):
    """Test suite for academic citation formats."""

    def setUp(self):
        self.sample_meta = PaperMetadata(
            title="Vibe coding: programming through conversation with artificial intelligence",
            authors=["Advait Sarkar", "Ian Drosos"],
            year="2025",
            identifier="arXiv:2506.23253",
            url="https://arxiv.org/abs/2506.23253",
            journal_or_venue="PPIG 2025",
        )

    def test_all_10_standards_generated(self):
        citations = generate_10_citations(self.sample_meta)
        expected_keys = [
            "BibTeX",
            "APA 7",
            "IEEE",
            "MLA 9",
            "Chicago",
            "Harvard",
            "Vancouver",
            "İSNAD 2",
            "RIS",
            "Plain Web",
        ]
        for key in expected_keys:
            self.assertIn(key, citations)
            self.assertTrue(len(citations[key]) > 0)

    def test_bibtex_format(self):
        citations = generate_10_citations(self.sample_meta)
        bibtex = citations["BibTeX"]
        self.assertTrue(bibtex.startswith("@article{"))
        self.assertIn("author    = {Advait Sarkar and Ian Drosos}", bibtex)
        self.assertIn("title     = {{Vibe coding: programming through conversation with artificial intelligence}}", bibtex)

    def test_isnad2_format(self):
        citations = generate_10_citations(self.sample_meta)
        isnad = citations["İSNAD 2"]
        # İSNAD format: Soyadı, Adı. "Başlık". Dergi (Yıl)
        self.assertIn("Sarkar, Advait", isnad)
        self.assertIn('"Vibe coding', isnad)
        self.assertIn("2025", isnad)

    def test_ris_format(self):
        citations = generate_10_citations(self.sample_meta)
        ris = citations["RIS"]
        self.assertTrue(ris.startswith("TY  - JOUR"))
        self.assertIn("AU  - Sarkar, Advait", ris)
        self.assertIn("ER  -", ris)

    def test_markdown_details_block(self):
        citations = generate_10_citations(self.sample_meta)
        md_block = format_citations_markdown(citations)
        self.assertIn("<details>", md_block)
        self.assertIn("İSNAD 2", md_block)
        self.assertIn("BibTeX", md_block)


if __name__ == "__main__":
    unittest.main()
