"""Unit tests for the TextProcessor class."""

import os
import tempfile
import unittest

import yaml

from src.core.config import Config
from src.transcription.text_processor import TextProcessor


class TestTextProcessor(unittest.TestCase):
    """Test cases for TextProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file with test settings
        self.config_data = {
            "text_processing": {
                "punctuation_commands": True,
                "punctuation_map": {
                    "period": ".",
                    "comma": ",",
                    "question mark": "?",
                    "exclamation point": "!",
                    "new line": "\n",
                },
                "custom_vocabulary": {
                    "dictation tool": "DictationTool",
                    "my email": "test@example.com",
                },
                "command_words": {
                    "delete that": "undo_last",
                    "clear line": "clear_line",
                },
            },
            "advanced": {
                "log_level": "INFO",
            }
        }

        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.processor = TextProcessor(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_punctuation_replacement(self):
        """Test that punctuation commands are replaced correctly."""
        text, command = self.processor.process("Hello period How are you question mark")
        self.assertEqual(text, "Hello. How are you?")
        self.assertIsNone(command)

    def test_multiple_punctuation(self):
        """Test multiple punctuation marks in one sentence."""
        text, command = self.processor.process("Yes comma I agree exclamation point")
        self.assertEqual(text, "Yes, I agree!")
        self.assertIsNone(command)

    def test_custom_vocabulary(self):
        """Test custom vocabulary replacement."""
        text, command = self.processor.process("I use dictation tool for my work")
        self.assertEqual(text, "I use DictationTool for my work")
        self.assertIsNone(command)

    def test_command_word_detection(self):
        """Test that command words are detected and not typed."""
        text, command = self.processor.process("delete that")
        self.assertIsNone(text)
        self.assertEqual(command, "undo_last")

    def test_command_word_case_insensitive(self):
        """Test that command words work regardless of case."""
        text, command = self.processor.process("DELETE THAT")
        self.assertIsNone(text)
        self.assertEqual(command, "undo_last")

    def test_clear_line_command(self):
        """Test clear line command."""
        text, command = self.processor.process("clear line")
        self.assertIsNone(text)
        self.assertEqual(command, "clear_line")

    def test_combined_features(self):
        """Test punctuation and custom vocabulary together."""
        text, command = self.processor.process("Use dictation tool period It works great exclamation point")
        self.assertEqual(text, "Use DictationTool. It works great!")
        self.assertIsNone(command)

    def test_empty_text(self):
        """Test processing empty text."""
        text, command = self.processor.process("")
        self.assertIsNone(text)
        self.assertIsNone(command)

    def test_last_text_tracking(self):
        """Test that last text is tracked correctly."""
        text1, _ = self.processor.process("Hello world")
        self.assertEqual(self.processor.last_text, "Hello world")
        self.assertEqual(self.processor.get_last_text_length(), 11)

        text2, _ = self.processor.process("New text")
        self.assertEqual(self.processor.last_text, "New text")
        self.assertEqual(self.processor.get_last_text_length(), 8)

    def test_newline_punctuation(self):
        """Test new line punctuation command."""
        text, command = self.processor.process("First line new line Second line")
        self.assertEqual(text, "First line\nSecond line")
        self.assertIsNone(command)

    def test_punctuation_space_cleanup(self):
        """Test that extra spaces around punctuation are removed."""
        text, command = self.processor.process("Hello  comma  world  period")
        self.assertEqual(text, "Hello, world.")
        self.assertIsNone(command)

    def test_case_insensitive_punctuation(self):
        """Test that punctuation commands work with different cases."""
        text, command = self.processor.process("Hello PERIOD World COMMA Test")
        self.assertEqual(text, "Hello. World, Test")
        self.assertIsNone(command)


if __name__ == '__main__':
    unittest.main()
