"""Command parser with fuzzy matching and number extraction."""

import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional

import yaml


# Constants for parser configuration
DEFAULT_IGNORED_WORDS = ["thank", "you", "thanks", "please"]
DEFAULT_FUZZY_THRESHOLD = 0.8
NUMBER_MAPPINGS_FILENAME = "number_mappings.yaml"


class CommandParser:
    """
    Parser for voice commands with fuzzy matching and number extraction.

    Handles:
    - Number parsing with homophones (e.g., "to" -> 2, "for" -> 4)
    - Filler word removal (e.g., "please", "thank you")
    - Fuzzy string matching for command variations
    - Text normalization for consistent matching

    Example:
        ```python
        parser = CommandParser()

        # Extract numbers from text
        numbers = parser.extract_numbers("click to left for right")  # [2, 4]

        # Check if text is a single number
        is_num = parser.is_lone_number("five")  # True

        # Filter filler words
        clean = parser.filter_ignored_words("please click five")  # "click five"

        # Fuzzy match
        score = parser.fuzzy_match("click 5", "click number 5")  # High score
        ```
    """

    def __init__(
        self,
        number_mappings: Optional[Dict[str, int]] = None,
        ignored_words: Optional[List[str]] = None,
    ):
        """
        Initialize the command parser.

        Args:
            number_mappings: Optional custom number word mappings
                            (loads from number_mappings.yaml if not provided)
            ignored_words: Optional custom list of words to filter
                          (uses DEFAULT_IGNORED_WORDS if not provided)
        """
        self.number_mappings = number_mappings or self._load_number_mappings()
        self.ignored_words = set(ignored_words or DEFAULT_IGNORED_WORDS)

    def _load_number_mappings(self) -> Dict[str, int]:
        """
        Load number word mappings from number_mappings.yaml.

        Returns:
            Dictionary mapping number words (including homophones) to integers
        """
        try:
            # Get project root (3 levels up from src/commands/parser.py)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            mappings_file = os.path.join(project_root, NUMBER_MAPPINGS_FILENAME)
            with open(mappings_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("number_words", {})
        except FileNotFoundError:
            # Fallback to basic mappings
            return {
                "zero": 0,
                "oh": 0,
                "one": 1,
                "won": 1,
                "two": 2,
                "to": 2,
                "too": 2,
                "three": 3,
                "tree": 3,
                "four": 4,
                "for": 4,
                "fore": 4,
                "five": 5,
                "six": 6,
                "sicks": 6,
                "seven": 7,
                "eight": 8,
                "ate": 8,
                "nine": 9,
                "nein": 9,
                "ten": 10,
                "a": 1,
                "an": 1,
            }
        except Exception:
            return {}

    def extract_numbers(self, text: str) -> List[int]:
        """
        Extract numbers from text, supporting both digits and word numbers.

        Prioritizes digit numbers over word numbers. Uses loaded number mappings
        including homophones (e.g., "to"->2, "for"->4, "ate"->8).
        Handles compound numbers like "sixty-nine" -> 69.

        Args:
            text: Text containing numbers (e.g., "to left for right" or "2 left 4 right")

        Returns:
            List of integers found in the text

        Example:
            >>> parser.extract_numbers("click 5")
            [5]
            >>> parser.extract_numbers("to left for right")
            [2, 4]
            >>> parser.extract_numbers("move a left")
            [1]
            >>> parser.extract_numbers("sixty nine")
            [69]
        """
        numbers = []

        # First try to find digit numbers
        digit_numbers = re.findall(r"\d+", text)
        if digit_numbers:
            return [int(n) for n in digit_numbers]

        # If no digits, try word numbers (including homophones)
        words = text.lower().split()
        i = 0
        while i < len(words):
            word = words[i]
            if word in self.number_mappings:
                num = self.number_mappings[word]

                # Check for compound numbers (e.g., "sixty nine" -> 69)
                # If current number is a tens (20, 30, ..., 90) and next word is a units (1-9)
                if num >= 20 and num <= 90 and num % 10 == 0:
                    if i + 1 < len(words) and words[i + 1] in self.number_mappings:
                        next_num = self.number_mappings[words[i + 1]]
                        if 1 <= next_num <= 9:
                            # Combine tens + units
                            numbers.append(num + next_num)
                            i += 2  # Skip both words
                            continue

                numbers.append(num)
            i += 1

        return numbers

    def contains_numbers(self, text: str) -> bool:
        """
        Check if text contains numbers (either digits or number words).

        Args:
            text: Text to check

        Returns:
            True if text contains digits or number words from mappings

        Example:
            >>> parser.contains_numbers("click 5")
            True
            >>> parser.contains_numbers("click for me")
            True  # "for" is a homophone for 4
            >>> parser.contains_numbers("click here")
            False
        """
        # Check for digit characters
        if any(c.isdigit() for c in text):
            return True

        # Check for number words
        words = text.lower().split()
        for word in words:
            if word in self.number_mappings:
                return True

        return False

    def is_lone_number(self, text: str) -> bool:
        """
        Check if text is a single number (digit or number word).

        Args:
            text: Text to check

        Returns:
            True if text is just a single number

        Example:
            >>> parser.is_lone_number("5")
            True
            >>> parser.is_lone_number("five")
            True
            >>> parser.is_lone_number("click 5")
            False
        """
        text = text.strip()

        # Check if it's a digit number
        if text.isdigit():
            return True

        # Check if it's a single number word
        if text.lower() in self.number_mappings:
            return True

        return False

    def parse_number(self, text: str) -> Optional[int]:
        """
        Parse a single number from text (digit or number word).

        Args:
            text: Text containing a single number

        Returns:
            Integer value or None if not a valid number

        Example:
            >>> parser.parse_number("5")
            5
            >>> parser.parse_number("five")
            5
            >>> parser.parse_number("for")
            4  # Homophone for "four"
            >>> parser.parse_number("hello")
            None
        """
        text = text.strip()

        # Try parsing as digit
        if text.isdigit():
            return int(text)

        # Try parsing as number word
        if text.lower() in self.number_mappings:
            return self.number_mappings[text.lower()]

        return None

    def filter_ignored_words(self, text: str) -> str:
        """
        Remove ignored filler/politeness words from text.

        Args:
            text: Original text

        Returns:
            Filtered text with ignored words removed

        Example:
            >>> parser.filter_ignored_words("please click five")
            "click five"
            >>> parser.filter_ignored_words("thank you for clicking")
            "for clicking"
        """
        words = text.split()
        filtered_words = []

        for word in words:
            # Strip punctuation from word for comparison
            word_clean = word.strip(".,!?;:").lower()
            if word_clean not in self.ignored_words:
                filtered_words.append(word)

        return " ".join(filtered_words).strip()

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent matching.

        Performs:
        - Convert to lowercase
        - Remove extra whitespace
        - Remove common punctuation

        Args:
            text: Text to normalize

        Returns:
            Normalized text

        Example:
            >>> parser.normalize_text("  Click   5!  ")
            "click 5"
        """
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation (but keep hyphens and apostrophes)
        text = re.sub(r"[^\w\s\-']", "", text)

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def fuzzy_match(
        self,
        text1: str,
        text2: str,
        threshold: float = DEFAULT_FUZZY_THRESHOLD,
        normalize: bool = True,
    ) -> float:
        """
        Calculate fuzzy similarity between two strings.

        Uses SequenceMatcher to compute similarity ratio. Useful for handling
        slight variations in voice commands.

        Args:
            text1: First text string
            text2: Second text string
            threshold: Minimum similarity threshold (0.0 to 1.0)
            normalize: Whether to normalize text before matching

        Returns:
            Similarity score from 0.0 (no match) to 1.0 (exact match)

        Example:
            >>> parser.fuzzy_match("click 5", "click number 5")
            0.8  # High similarity
            >>> parser.fuzzy_match("click", "scroll")
            0.0  # Low similarity
        """
        if normalize:
            text1 = self.normalize_text(text1)
            text2 = self.normalize_text(text2)

        return SequenceMatcher(None, text1, text2).ratio()

    def is_fuzzy_match(
        self,
        text1: str,
        text2: str,
        threshold: float = DEFAULT_FUZZY_THRESHOLD,
        normalize: bool = True,
    ) -> bool:
        """
        Check if two strings fuzzy match above a threshold.

        Args:
            text1: First text string
            text2: Second text string
            threshold: Minimum similarity threshold (0.0 to 1.0)
            normalize: Whether to normalize text before matching

        Returns:
            True if similarity score >= threshold

        Example:
            >>> parser.is_fuzzy_match("click 5", "click number 5", threshold=0.7)
            True
            >>> parser.is_fuzzy_match("click", "scroll", threshold=0.7)
            False
        """
        score = self.fuzzy_match(text1, text2, threshold, normalize)
        return score >= threshold

    def extract_pattern(self, text: str, pattern: str) -> Optional[re.Match]:
        """
        Extract pattern from text using regex.

        Args:
            text: Text to search
            pattern: Regex pattern to match

        Returns:
            Match object if pattern found, None otherwise

        Example:
            >>> match = parser.extract_pattern("click 5", r"click (\\d+)")
            >>> match.group(1)
            '5'
        """
        return re.search(pattern, text, re.IGNORECASE)

    def split_command_and_args(self, text: str) -> tuple[str, str]:
        """
        Split text into command word and arguments.

        Args:
            text: Command text (e.g., "click 5", "scroll down")

        Returns:
            Tuple of (command_word, arguments)

        Example:
            >>> parser.split_command_and_args("click 5")
            ("click", "5")
            >>> parser.split_command_and_args("scroll down fast")
            ("scroll", "down fast")
        """
        parts = text.strip().split(maxsplit=1)
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]
