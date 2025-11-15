"""Text processing for dictation with punctuation commands and custom vocabulary."""

import re
from typing import Optional, Tuple

from src.core.config import Config


class TextProcessor:
    """
    Process transcribed text with punctuation commands and custom vocabulary.

    Handles:
    - Punctuation command replacement (e.g., "period" -> ".")
    - Custom vocabulary substitutions
    - Command word detection (e.g., "delete that", "clear line")
    """

    def __init__(self, config: Config):
        """
        Initialize the text processor.

        Args:
            config: Configuration object containing text processing settings
        """
        self.config = config
        self.punctuation_map = config.get("text_processing", "punctuation_map", default={})
        self.custom_vocabulary = config.get("text_processing", "custom_vocabulary", default={})
        self.command_words = config.get("text_processing", "command_words", default={})
        self.last_text = ""

    def process(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Process text with punctuation commands and custom vocabulary.

        Args:
            text: Transcribed text to process

        Returns:
            Tuple of (processed_text, command_action)
            - processed_text: Text to type (None if command word detected)
            - command_action: Command to execute (None if regular text)
        """
        if not text:
            return None, None

        # Check for command words
        text_lower = text.lower().strip()
        if text_lower in self.command_words:
            command = self.command_words[text_lower]
            return None, command  # Don't type command words, return command action

        # Apply punctuation commands
        if self.config.get("text_processing", "punctuation_commands", default=True):
            text = self._apply_punctuation_commands(text)

        # Apply custom vocabulary
        text = self._apply_custom_vocabulary(text)

        self.last_text = text
        return text, None

    def _apply_punctuation_commands(self, text: str) -> str:
        """
        Replace spoken punctuation with actual punctuation marks.

        Args:
            text: Text containing spoken punctuation

        Returns:
            Text with punctuation marks substituted
        """
        if not self.punctuation_map:
            return text

        # Sort by length descending to avoid partial matches (e.g., "period" before "per")
        words = sorted(self.punctuation_map.keys(), key=len, reverse=True)
        pattern = r"\b(" + "|".join(map(re.escape, words)) + r")\b"

        def repl(match):
            word = match.group(0)
            # Use original case-insensitive mapping
            for k in self.punctuation_map:
                if word.lower() == k.lower():
                    return self.punctuation_map[k]
            return word

        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # Clean up extra spaces around punctuation (but preserve newlines)
        text = re.sub(r"[ \t]+([.,!?;:])", r"\1", text)  # Remove spaces before punctuation (not newlines)
        text = re.sub(r"[ \t]+", " ", text)  # Collapse multiple spaces (not newlines)
        text = re.sub(r"[ \t]+\n", r"\n", text)  # Remove spaces before newlines
        text = re.sub(r"\n[ \t]+", r"\n", text)  # Remove spaces after newlines
        return text.strip()

    def _apply_custom_vocabulary(self, text: str) -> str:
        """
        Apply custom vocabulary replacements.

        Args:
            text: Text to process

        Returns:
            Text with custom vocabulary substitutions
        """
        for phrase, replacement in self.custom_vocabulary.items():
            text = re.sub(r"\b" + re.escape(phrase) + r"\b", replacement, text, flags=re.IGNORECASE)
        return text

    def get_last_text_length(self) -> int:
        """
        Get the length of the last processed text.

        Returns:
            Length of last text (for undo operations)
        """
        return len(self.last_text)
