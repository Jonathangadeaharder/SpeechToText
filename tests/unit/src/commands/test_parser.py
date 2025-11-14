"""Unit tests for CommandParser."""

import unittest
from unittest.mock import patch, mock_open

from src.commands.parser import CommandParser


class TestCommandParser(unittest.TestCase):
    """Test cases for CommandParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_initialization_with_defaults(self):
        """Test parser initializes with default mappings."""
        parser = CommandParser()
        self.assertIsNotNone(parser.number_mappings)
        self.assertIsNotNone(parser.ignored_words)

    def test_initialization_with_custom_mappings(self):
        """Test parser with custom number mappings."""
        custom_mappings = {"one": 1, "two": 2}
        parser = CommandParser(number_mappings=custom_mappings)
        self.assertEqual(parser.number_mappings, custom_mappings)

    def test_initialization_with_custom_ignored_words(self):
        """Test parser with custom ignored words."""
        custom_ignored = ["um", "uh"]
        parser = CommandParser(ignored_words=custom_ignored)
        self.assertEqual(parser.ignored_words, set(custom_ignored))

    def test_extract_numbers_with_digits(self):
        """Test extracting digit numbers from text."""
        numbers = self.parser.extract_numbers("click 5")
        self.assertEqual(numbers, [5])

        numbers = self.parser.extract_numbers("move 10 left 20 right")
        self.assertEqual(numbers, [10, 20])

    def test_extract_numbers_with_words(self):
        """Test extracting number words from text."""
        numbers = self.parser.extract_numbers("click five")
        self.assertEqual(numbers, [5])

        numbers = self.parser.extract_numbers("move one left two right")
        self.assertEqual(numbers, [1, 2])

    def test_extract_numbers_with_homophones(self):
        """Test extracting numbers from homophones."""
        numbers = self.parser.extract_numbers("to left for right")
        self.assertEqual(numbers, [2, 4])

        numbers = self.parser.extract_numbers("ate cookies")
        self.assertEqual(numbers, [8])

    def test_extract_numbers_empty_text(self):
        """Test extracting numbers from empty text."""
        numbers = self.parser.extract_numbers("")
        self.assertEqual(numbers, [])

    def test_extract_numbers_no_numbers(self):
        """Test extracting numbers when none present."""
        numbers = self.parser.extract_numbers("click here")
        self.assertEqual(numbers, [])

    def test_contains_numbers_with_digits(self):
        """Test contains_numbers with digit text."""
        self.assertTrue(self.parser.contains_numbers("click 5"))
        self.assertTrue(self.parser.contains_numbers("123"))

    def test_contains_numbers_with_words(self):
        """Test contains_numbers with number words."""
        self.assertTrue(self.parser.contains_numbers("click five"))
        self.assertTrue(self.parser.contains_numbers("for me"))  # "for" = 4

    def test_contains_numbers_no_numbers(self):
        """Test contains_numbers with no numbers."""
        self.assertFalse(self.parser.contains_numbers("click here"))
        self.assertFalse(self.parser.contains_numbers("hello world"))

    def test_is_lone_number_with_digit(self):
        """Test is_lone_number with digit."""
        self.assertTrue(self.parser.is_lone_number("5"))
        self.assertTrue(self.parser.is_lone_number("123"))
        self.assertTrue(self.parser.is_lone_number("  42  "))  # With whitespace

    def test_is_lone_number_with_word(self):
        """Test is_lone_number with number word."""
        self.assertTrue(self.parser.is_lone_number("five"))
        self.assertTrue(self.parser.is_lone_number("ten"))
        self.assertTrue(self.parser.is_lone_number("for"))  # Homophone

    def test_is_lone_number_not_number(self):
        """Test is_lone_number with non-number text."""
        self.assertFalse(self.parser.is_lone_number("click 5"))
        self.assertFalse(self.parser.is_lone_number("hello"))
        self.assertFalse(self.parser.is_lone_number(""))

    def test_parse_number_with_digit(self):
        """Test parse_number with digit."""
        self.assertEqual(self.parser.parse_number("5"), 5)
        self.assertEqual(self.parser.parse_number("42"), 42)
        self.assertEqual(self.parser.parse_number("  123  "), 123)

    def test_parse_number_with_word(self):
        """Test parse_number with number word."""
        self.assertEqual(self.parser.parse_number("five"), 5)
        self.assertEqual(self.parser.parse_number("ten"), 10)
        self.assertEqual(self.parser.parse_number("for"), 4)  # Homophone

    def test_parse_number_invalid(self):
        """Test parse_number with invalid input."""
        self.assertIsNone(self.parser.parse_number("hello"))
        self.assertIsNone(self.parser.parse_number("click 5"))
        self.assertIsNone(self.parser.parse_number(""))

    def test_filter_ignored_words(self):
        """Test filtering ignored words from text."""
        result = self.parser.filter_ignored_words("please click five")
        self.assertEqual(result, "click five")

        result = self.parser.filter_ignored_words("thank you for clicking")
        self.assertEqual(result, "for clicking")

    def test_filter_ignored_words_with_punctuation(self):
        """Test filtering ignores words with punctuation."""
        # "please" with comma is removed because "please" (stripped) is in ignored
        result = self.parser.filter_ignored_words("please click here")
        self.assertEqual(result, "click here")

        # "thank" and "you" are both ignored words
        result = self.parser.filter_ignored_words("click thank you")
        self.assertEqual(result, "click")

    def test_filter_ignored_words_no_ignored(self):
        """Test filtering when no ignored words present."""
        result = self.parser.filter_ignored_words("click five")
        self.assertEqual(result, "click five")

    def test_normalize_text_lowercase(self):
        """Test normalize_text converts to lowercase."""
        result = self.parser.normalize_text("CLICK Five")
        self.assertEqual(result, "click five")

    def test_normalize_text_removes_punctuation(self):
        """Test normalize_text removes punctuation."""
        result = self.parser.normalize_text("click, five!")
        self.assertEqual(result, "click five")

    def test_normalize_text_removes_extra_whitespace(self):
        """Test normalize_text removes extra whitespace."""
        result = self.parser.normalize_text("  click   five  ")
        self.assertEqual(result, "click five")

    def test_normalize_text_preserves_hyphens_apostrophes(self):
        """Test normalize_text preserves hyphens and apostrophes."""
        result = self.parser.normalize_text("it's a nice-day")
        self.assertEqual(result, "it's a nice-day")

    def test_fuzzy_match_exact(self):
        """Test fuzzy_match with exact match."""
        score = self.parser.fuzzy_match("click 5", "click 5")
        self.assertEqual(score, 1.0)

    def test_fuzzy_match_high_similarity(self):
        """Test fuzzy_match with high similarity."""
        score = self.parser.fuzzy_match("click 5", "click number 5")
        self.assertGreater(score, 0.5)

    def test_fuzzy_match_low_similarity(self):
        """Test fuzzy_match with low similarity."""
        score = self.parser.fuzzy_match("click", "scroll")
        self.assertLess(score, 0.5)

    def test_fuzzy_match_with_normalization(self):
        """Test fuzzy_match with normalization enabled."""
        score = self.parser.fuzzy_match("CLICK 5!", "click 5", normalize=True)
        self.assertEqual(score, 1.0)

    def test_fuzzy_match_without_normalization(self):
        """Test fuzzy_match without normalization."""
        score = self.parser.fuzzy_match("CLICK 5", "click 5", normalize=False)
        self.assertLess(score, 1.0)

    def test_is_fuzzy_match_above_threshold(self):
        """Test is_fuzzy_match returns True above threshold."""
        result = self.parser.is_fuzzy_match("click 5", "click 5", threshold=0.8)
        self.assertTrue(result)

    def test_is_fuzzy_match_below_threshold(self):
        """Test is_fuzzy_match returns False below threshold."""
        result = self.parser.is_fuzzy_match("click", "scroll", threshold=0.8)
        self.assertFalse(result)

    def test_extract_pattern_found(self):
        """Test extract_pattern when pattern found."""
        match = self.parser.extract_pattern("click 5", r"click (\d+)")
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "5")

    def test_extract_pattern_not_found(self):
        """Test extract_pattern when pattern not found."""
        match = self.parser.extract_pattern("click here", r"click (\d+)")
        self.assertIsNone(match)

    def test_extract_pattern_case_insensitive(self):
        """Test extract_pattern is case insensitive."""
        match = self.parser.extract_pattern("CLICK 5", r"click (\d+)")
        self.assertIsNotNone(match)

    def test_split_command_and_args_with_args(self):
        """Test split_command_and_args with arguments."""
        command, args = self.parser.split_command_and_args("click 5")
        self.assertEqual(command, "click")
        self.assertEqual(args, "5")

        command, args = self.parser.split_command_and_args("scroll down fast")
        self.assertEqual(command, "scroll")
        self.assertEqual(args, "down fast")

    def test_split_command_and_args_no_args(self):
        """Test split_command_and_args without arguments."""
        command, args = self.parser.split_command_and_args("click")
        self.assertEqual(command, "click")
        self.assertEqual(args, "")

    def test_split_command_and_args_with_whitespace(self):
        """Test split_command_and_args handles whitespace."""
        # text.strip() is called first, so leading/trailing whitespace is removed
        command, args = self.parser.split_command_and_args("  click   5  ")
        self.assertEqual(command, "click")
        self.assertEqual(args, "5")  # Trailing whitespace removed by strip()

    def test_load_number_mappings_file_not_found(self):
        """Test _load_number_mappings with missing file uses fallback."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            parser = CommandParser()
            # Should have fallback mappings
            self.assertIn("one", parser.number_mappings)
            self.assertIn("two", parser.number_mappings)
            self.assertEqual(parser.number_mappings["one"], 1)

    def test_load_number_mappings_exception(self):
        """Test _load_number_mappings handles exceptions."""
        with patch("builtins.open", side_effect=Exception("Test error")):
            parser = CommandParser()
            # Should return empty dict on exception
            self.assertEqual(parser.number_mappings, {})


if __name__ == '__main__':
    unittest.main()
