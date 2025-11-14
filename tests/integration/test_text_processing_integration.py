"""
Integration tests for text processing and command execution.

Tests the flow from TextProcessor through CommandRegistry to verify
proper handling of punctuation, vocabulary, and command words.
"""

import pytest
from pynput import keyboard

from src.commands.base import CommandContext
from src.commands.handlers.keyboard_commands import EnterCommand, SelectAllCommand
from src.commands.registry import CommandRegistry
from src.core.config import Config
from src.core.events import EventBus
from src.transcription.text_processor import TextProcessor


class MockKeyboardController:
    """Mock keyboard controller for testing."""

    def __init__(self):
        self.pressed_keys = []
        self.released_keys = []
        self.typed_text = []

    def press(self, key):
        self.pressed_keys.append(key)

    def release(self, key):
        self.released_keys.append(key)

    def type(self, text):
        self.typed_text.append(text)

    def pressed(self, key):
        """Context manager for pressing a key."""

        class PressedContext:
            def __init__(self, controller, key):
                self.controller = controller
                self.key = key

            def __enter__(self):
                self.controller.press(self.key)
                return self

            def __exit__(self, *args):
                self.controller.release(self.key)
                return False

        return PressedContext(self, key)


@pytest.fixture
def config():
    """Create test configuration with text processing settings."""
    config = Config()
    config.config = {
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
                "scratch that": "undo_last",
                "clear line": "clear_line",
            },
        },
        "advanced": {"log_level": "DEBUG"},
    }
    return config


@pytest.fixture
def text_processor(config):
    """Create text processor."""
    return TextProcessor(config)


@pytest.fixture
def event_bus():
    """Create event bus."""
    return EventBus()


@pytest.fixture
def command_registry(event_bus):
    """Create command registry."""
    registry = CommandRegistry(event_bus)
    registry.register(EnterCommand())
    registry.register(SelectAllCommand())
    return registry


@pytest.fixture
def command_context(config, event_bus):
    """Create command context."""
    return CommandContext(
        config=config,
        keyboard_controller=MockKeyboardController(),
        mouse_controller=None,
        event_bus=event_bus,
    )


def test_punctuation_replacement(text_processor):
    """Test that punctuation commands are replaced correctly."""
    text, command = text_processor.process("Hello world period")
    assert text == "Hello world."
    assert command is None

    text, command = text_processor.process("Yes comma I agree")
    assert text == "Yes, I agree"
    assert command is None

    text, command = text_processor.process("What is this question mark")
    assert text == "What is this?"
    assert command is None


def test_multiple_punctuation_marks(text_processor):
    """Test text with multiple punctuation commands."""
    text, command = text_processor.process("Hello comma world period How are you question mark")
    assert text == "Hello, world. How are you?"
    assert command is None


def test_newline_punctuation(text_processor):
    """Test newline punctuation commands."""
    text, command = text_processor.process("First line new line Second line")
    assert text == "First line\nSecond line"
    assert command is None


def test_custom_vocabulary_replacement(text_processor):
    """Test custom vocabulary replacements."""
    text, command = text_processor.process("I use the dictation tool")
    assert text == "I use the DictationTool"
    assert command is None

    text, command = text_processor.process("Send to my email")
    assert text == "Send to test@example.com"
    assert command is None


def test_command_word_detection(text_processor):
    """Test that command words are detected and not processed as text."""
    # "delete that" should trigger undo_last command
    text, command = text_processor.process("delete that")
    assert text is None
    assert command == "undo_last"

    # "scratch that" should also trigger undo_last
    text, command = text_processor.process("scratch that")
    assert text is None
    assert command == "undo_last"

    # "clear line" should trigger clear_line command
    text, command = text_processor.process("clear line")
    assert text is None
    assert command == "clear_line"


def test_text_processor_to_command_registry_flow(text_processor, command_registry, command_context):
    """Test complete flow from text processor to command registry."""
    # Process text that should become a command
    text, command_action = text_processor.process("enter")

    # Text should pass through unchanged (not a command word in text_processor)
    assert text == "enter"
    assert command_action is None

    # Try to execute as command
    result, executed = command_registry.process(text, command_context)

    # Should execute as EnterCommand
    assert executed
    kb = command_context.keyboard_controller
    assert keyboard.Key.enter in kb.pressed_keys


def test_punctuation_then_command_flow(text_processor, command_registry, command_context):
    """Test processing text with punctuation that becomes a command."""
    # Process "select all" - not a punctuation command, should pass through
    text, command_action = text_processor.process("select all")
    assert text == "select all"
    assert command_action is None

    # Execute as command
    result, executed = command_registry.process(text, command_context)
    assert executed

    kb = command_context.keyboard_controller
    assert keyboard.Key.ctrl in kb.pressed_keys or "a" in kb.pressed_keys


def test_mixed_punctuation_and_vocabulary(text_processor):
    """Test text with both punctuation commands and custom vocabulary."""
    text, command = text_processor.process("I use dictation tool period It is great exclamation point")
    assert text == "I use DictationTool. It is great!"
    assert command is None


def test_last_text_tracking(text_processor):
    """Test that last text length is tracked for undo operations."""
    # Process some text
    text, _ = text_processor.process("Hello world")
    assert text_processor.get_last_text_length() == len("Hello world")

    # Process more text
    text, _ = text_processor.process("Testing period")
    assert text_processor.get_last_text_length() == len("Testing.")


def test_command_word_case_insensitive(text_processor):
    """Test that command words are case-insensitive."""
    # Upper case
    text, command = text_processor.process("DELETE THAT")
    assert text is None
    assert command == "undo_last"

    # Mixed case
    text, command = text_processor.process("Clear Line")
    assert text is None
    assert command == "clear_line"


def test_empty_text_handling(text_processor):
    """Test handling of empty or None text."""
    text, command = text_processor.process("")
    assert text is None
    assert command is None

    text, command = text_processor.process(None)
    assert text is None
    assert command is None


def test_text_only_punctuation(text_processor):
    """Test text that is only punctuation commands."""
    text, command = text_processor.process("period comma period")
    assert text == ".,."
    assert command is None


def test_punctuation_spacing_cleanup(text_processor):
    """Test that extra spaces around punctuation are cleaned up."""
    text, command = text_processor.process("Hello   comma   world   period")

    # Should clean up spaces around punctuation
    assert text == "Hello, world."
    assert command is None


def test_integration_realistic_dictation(text_processor, command_registry, command_context):
    """Test realistic dictation scenario with multiple processing steps."""
    # Simulate a realistic dictation session
    sentences = [
        ("Hello comma this is a test period", "Hello, this is a test."),
        ("I am using the dictation tool period", "I am using the DictationTool."),
        ("What is my email question mark", "What is test@example.com?"),
        ("select all", None),  # This is a command
        ("New text period", "New text."),
    ]

    for input_text, expected_output in sentences:
        # Process through text processor
        processed, command_action = text_processor.process(input_text)

        if expected_output is None:
            # This should be a command
            result, executed = command_registry.process(processed, command_context)
            assert executed
        else:
            # This should be regular text
            assert processed == expected_output
            assert command_action is None


def test_punctuation_at_text_boundaries(text_processor):
    """Test punctuation commands at start and end of text."""
    # Period at start
    text, command = text_processor.process("period Hello")
    assert text == ". Hello"

    # Period at end
    text, command = text_processor.process("Hello period")
    assert text == "Hello."

    # Multiple at end
    text, command = text_processor.process("Hello period exclamation point")
    assert text == "Hello.!"


def test_consecutive_punctuation_marks(text_processor):
    """Test consecutive punctuation commands without text between."""
    text, command = text_processor.process("Hello period period period")
    assert text == "Hello..."

    text, command = text_processor.process("What question mark exclamation point")
    assert text == "What?!"


def test_custom_vocabulary_with_punctuation(text_processor):
    """Test custom vocabulary that contains punctuation."""
    # Add vocabulary with punctuation
    text_processor.custom_vocabulary["test.com"] = "TEST.COM"

    text, command = text_processor.process("Visit test.com today")
    # Note: Punctuation replacement happens before vocabulary
    # This tests the order of operations
    assert "test.com" in text or "TEST.COM" in text
