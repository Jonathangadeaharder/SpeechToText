"""Unit tests for keyboard command implementations."""

import os
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch, call

import yaml
from pynput import keyboard

from src.commands.handlers.keyboard_commands import (
    BackspaceCommand,
    ClipboardCommand,
    EnterCommand,
    EscapeCommand,
    RedoCommand,
    SaveCommand,
    SelectAllCommand,
    SpaceCommand,
    TabCommand,
    TypeSymbolCommand,
    UndoCommand,
)
from src.commands.base import CommandContext
from src.core.config import Config
from src.core.events import EventBus, EventType


def create_mock_keyboard():
    """Create a mock keyboard controller that supports context manager protocol."""
    mock = Mock(spec=keyboard.Controller)
    # Configure the mock to support context manager protocol
    mock.pressed.return_value.__enter__ = Mock(return_value=None)
    mock.pressed.return_value.__exit__ = Mock(return_value=False)
    return mock


class TestKeyPressCommands(unittest.TestCase):
    """Test cases for basic key press commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = create_mock_keyboard()
        self.mock_mouse = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_enter_command_matches(self):
        """Test Enter command matching."""
        cmd = EnterCommand()
        self.assertTrue(cmd.matches("enter"))
        self.assertTrue(cmd.matches("ENTER"))
        self.assertTrue(cmd.matches("  enter  "))
        self.assertFalse(cmd.matches("enter key"))

    def test_enter_command_execute(self):
        """Test Enter command execution."""
        cmd = EnterCommand()
        result = cmd.execute(self.context, "enter")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.enter)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.enter)

    def test_tab_command_matches(self):
        """Test Tab command matching."""
        cmd = TabCommand()
        self.assertTrue(cmd.matches("tab"))
        self.assertFalse(cmd.matches("table"))

    def test_tab_command_execute(self):
        """Test Tab command execution."""
        cmd = TabCommand()
        result = cmd.execute(self.context, "tab")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.tab)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.tab)

    def test_escape_command_matches(self):
        """Test Escape command matching."""
        cmd = EscapeCommand()
        self.assertTrue(cmd.matches("escape"))
        self.assertTrue(cmd.matches("cancel"))

    def test_escape_command_execute(self):
        """Test Escape command execution."""
        cmd = EscapeCommand()
        result = cmd.execute(self.context, "escape")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.esc)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.esc)

    def test_space_command_matches(self):
        """Test Space command matching."""
        cmd = SpaceCommand()
        self.assertTrue(cmd.matches("space"))

    def test_space_command_execute(self):
        """Test Space command execution."""
        cmd = SpaceCommand()
        result = cmd.execute(self.context, "space")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.space)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.space)

    def test_backspace_command_matches(self):
        """Test Backspace command matching."""
        cmd = BackspaceCommand()
        self.assertTrue(cmd.matches("delete"))
        self.assertTrue(cmd.matches("backspace"))

    def test_backspace_command_execute(self):
        """Test Backspace command execution."""
        cmd = BackspaceCommand()
        result = cmd.execute(self.context, "delete")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.backspace)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.backspace)

    def test_command_priorities(self):
        """Test that key commands have appropriate priorities."""
        self.assertEqual(EnterCommand().priority, 100)
        self.assertEqual(TabCommand().priority, 100)
        self.assertEqual(EscapeCommand().priority, 100)

    def test_command_descriptions(self):
        """Test that commands have descriptions."""
        self.assertIn("Enter", EnterCommand().description)
        self.assertIn("Tab", TabCommand().description)
        self.assertIn("Escape", EscapeCommand().description)

    def test_command_examples(self):
        """Test that commands provide examples."""
        self.assertIn("enter", EnterCommand().examples)
        self.assertIn("tab", TabCommand().examples)
        self.assertIn("escape", EscapeCommand().examples)


class TestClipboardCommand(unittest.TestCase):
    """Test cases for clipboard commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = create_mock_keyboard()
        self.mock_mouse = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_clipboard_command_matches(self):
        """Test clipboard command matching."""
        cmd = ClipboardCommand()
        self.assertTrue(cmd.matches("copy"))
        self.assertTrue(cmd.matches("cut"))
        self.assertTrue(cmd.matches("paste"))
        self.assertFalse(cmd.matches("clipboard"))

    def test_copy_command_execute(self):
        """Test copy command execution."""
        cmd = ClipboardCommand()
        result = cmd.execute(self.context, "copy")

        self.assertIsNone(result)
        # Should press Ctrl+C
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("c")
        self.mock_keyboard.release.assert_called_once_with("c")

    def test_cut_command_execute(self):
        """Test cut command execution."""
        cmd = ClipboardCommand()
        result = cmd.execute(self.context, "cut")

        self.assertIsNone(result)
        # Should press Ctrl+X
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("x")
        self.mock_keyboard.release.assert_called_once_with("x")

    def test_paste_command_execute(self):
        """Test paste command execution."""
        cmd = ClipboardCommand()
        result = cmd.execute(self.context, "paste")

        self.assertIsNone(result)
        # Should press Ctrl+V
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("v")
        self.mock_keyboard.release.assert_called_once_with("v")

    def test_clipboard_command_priority(self):
        """Test clipboard command has higher priority."""
        cmd = ClipboardCommand()
        self.assertEqual(cmd.priority, 200)

    def test_clipboard_command_examples(self):
        """Test clipboard command examples."""
        cmd = ClipboardCommand()
        self.assertEqual(cmd.examples, ["copy", "cut", "paste"])


class TestSelectAllCommand(unittest.TestCase):
    """Test cases for Select All command."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = create_mock_keyboard()
        self.mock_mouse = Mock()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_select_all_matches(self):
        """Test Select All command matching."""
        cmd = SelectAllCommand()
        self.assertTrue(cmd.matches("select all"))
        self.assertTrue(cmd.matches("SELECT ALL"))
        self.assertFalse(cmd.matches("select"))

    def test_select_all_execute(self):
        """Test Select All command execution."""
        cmd = SelectAllCommand()
        result = cmd.execute(self.context, "select all")

        self.assertIsNone(result)
        # Should press Ctrl+A
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("a")
        self.mock_keyboard.release.assert_called_once_with("a")


class TestUndoRedoCommands(unittest.TestCase):
    """Test cases for Undo/Redo commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = create_mock_keyboard()
        self.mock_mouse = Mock()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_undo_command_matches(self):
        """Test Undo command matching."""
        cmd = UndoCommand()
        self.assertTrue(cmd.matches("undo"))
        self.assertFalse(cmd.matches("redo"))

    def test_undo_command_execute(self):
        """Test Undo command execution."""
        cmd = UndoCommand()
        result = cmd.execute(self.context, "undo")

        self.assertIsNone(result)
        # Should press Ctrl+Z
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("z")
        self.mock_keyboard.release.assert_called_once_with("z")

    def test_redo_command_matches(self):
        """Test Redo command matching."""
        cmd = RedoCommand()
        self.assertTrue(cmd.matches("redo"))
        self.assertFalse(cmd.matches("undo"))

    def test_redo_command_execute(self):
        """Test Redo command execution."""
        cmd = RedoCommand()
        result = cmd.execute(self.context, "redo")

        self.assertIsNone(result)
        # Should press Ctrl+Y
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("y")
        self.mock_keyboard.release.assert_called_once_with("y")


class TestSaveCommand(unittest.TestCase):
    """Test cases for Save command."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = create_mock_keyboard()
        self.mock_mouse = Mock()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_save_command_matches(self):
        """Test Save command matching."""
        cmd = SaveCommand()
        self.assertTrue(cmd.matches("save"))
        self.assertFalse(cmd.matches("save file"))

    def test_save_command_execute(self):
        """Test Save command execution."""
        cmd = SaveCommand()
        result = cmd.execute(self.context, "save")

        self.assertIsNone(result)
        # Should press Ctrl+S
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with("s")
        self.mock_keyboard.release.assert_called_once_with("s")


class TestTypeSymbolCommand(unittest.TestCase):
    """Test cases for Type Symbol command."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = create_mock_keyboard()
        self.mock_mouse = Mock()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_type_symbol_matches(self):
        """Test symbol command matching."""
        cmd = TypeSymbolCommand()
        self.assertTrue(cmd.matches("slash"))
        self.assertTrue(cmd.matches("open paren"))
        self.assertTrue(cmd.matches("equals"))
        self.assertTrue(cmd.matches("comma"))
        self.assertFalse(cmd.matches("unknown"))

    def test_type_symbol_matches_with_type_prefix(self):
        """Test symbol command matching with 'type' prefix."""
        cmd = TypeSymbolCommand()
        self.assertTrue(cmd.matches("type slash"))
        self.assertTrue(cmd.matches("type semicolon"))
        self.assertTrue(cmd.matches("type comma"))
        self.assertTrue(cmd.matches("type equals"))
        self.assertFalse(cmd.matches("type unknown"))

    def test_type_symbol_execute_slash(self):
        """Test typing slash symbol."""
        cmd = TypeSymbolCommand()
        result = cmd.execute(self.context, "slash")
        self.assertEqual(result, "/")

    def test_type_symbol_execute_with_type_prefix(self):
        """Test typing symbols with 'type' prefix."""
        cmd = TypeSymbolCommand()
        self.assertEqual(cmd.execute(self.context, "type slash"), "/")
        self.assertEqual(cmd.execute(self.context, "type semicolon"), ";")
        self.assertEqual(cmd.execute(self.context, "type comma"), ",")
        self.assertEqual(cmd.execute(self.context, "type equals"), "=")

    def test_type_symbol_execute_parentheses(self):
        """Test typing parentheses."""
        cmd = TypeSymbolCommand()
        self.assertEqual(cmd.execute(self.context, "open paren"), "(")
        self.assertEqual(cmd.execute(self.context, "close paren"), ")")
        self.assertEqual(cmd.execute(self.context, "open"), "(")
        self.assertEqual(cmd.execute(self.context, "close"), ")")

    def test_type_symbol_execute_brackets(self):
        """Test typing brackets."""
        cmd = TypeSymbolCommand()
        self.assertEqual(cmd.execute(self.context, "open bracket"), "[")
        self.assertEqual(cmd.execute(self.context, "close bracket"), "]")
        self.assertEqual(cmd.execute(self.context, "open curly"), "{")
        self.assertEqual(cmd.execute(self.context, "close curly"), "}")

    def test_type_symbol_execute_punctuation(self):
        """Test typing punctuation."""
        cmd = TypeSymbolCommand()
        self.assertEqual(cmd.execute(self.context, "comma"), ",")
        self.assertEqual(cmd.execute(self.context, "period"), ".")
        self.assertEqual(cmd.execute(self.context, "question"), "?")
        self.assertEqual(cmd.execute(self.context, "exclamation"), "!")

    def test_type_symbol_execute_operators(self):
        """Test typing operators."""
        cmd = TypeSymbolCommand()
        self.assertEqual(cmd.execute(self.context, "plus"), "+")
        self.assertEqual(cmd.execute(self.context, "minus"), "-")
        self.assertEqual(cmd.execute(self.context, "equals"), "=")
        self.assertEqual(cmd.execute(self.context, "star"), "*")

    def test_type_symbol_homophones(self):
        """Test symbol homophones work."""
        cmd = TypeSymbolCommand()
        # These should all produce the same symbol
        self.assertEqual(cmd.execute(self.context, "dash"), "-")
        self.assertEqual(cmd.execute(self.context, "minus"), "-")

        self.assertEqual(cmd.execute(self.context, "dot"), ".")
        self.assertEqual(cmd.execute(self.context, "period"), ".")

    def test_type_symbol_priority(self):
        """Test symbol command priority."""
        cmd = TypeSymbolCommand()
        self.assertEqual(cmd.priority, 100)

    def test_type_symbol_examples(self):
        """Test symbol command provides examples."""
        cmd = TypeSymbolCommand()
        examples = cmd.examples
        self.assertIn("slash", examples)
        self.assertIn("comma", examples)


if __name__ == '__main__':
    unittest.main()
