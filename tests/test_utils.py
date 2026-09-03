"""Unit tests for pragmatic filename sanitization."""

import unittest
from paper_harvester.utils import sanitize_filename


class TestSanitizeFilename(unittest.TestCase):
    """Test suite for filename sanitization across operating systems."""

    def test_basic_clean_name(self):
        result = sanitize_filename("research_paper.pdf")
        self.assertEqual(result, "research_paper")

    def test_path_traversal_prevention(self):
        result = sanitize_filename("../../etc/passwd/paper.pdf")
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)
        self.assertNotIn("..", result)
        self.assertEqual(result, "paper")

    def test_invalid_filesystem_characters(self):
        result = sanitize_filename("cool:paper*name<v1>|test.pdf")
        for char in [":", "*", "<", ">", "|"]:
            self.assertNotIn(char, result)
        self.assertEqual(result, "cool_paper_name_v1_test")

    def test_url_with_query_params(self):
        result = sanitize_filename("https://arxiv.org/pdf/2512.11922.pdf?token=abc#section")
        self.assertEqual(result, "2512.11922")

    def test_empty_fallback(self):
        self.assertEqual(sanitize_filename("", fallback="document"), "document")
        self.assertEqual(sanitize_filename("   ", fallback="document"), "document")


if __name__ == "__main__":
    unittest.main()
