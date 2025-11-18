"""Unit tests for custom command implementations."""

import os
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch, call

import yaml
from pynput import keyboard

from src.commands.handlers.custom_commands import CustomCommand, load_custom_commands
from src.commands.base import CommandContext, PRIORITY_HIGH
from src.core.config import Config
from src.core.events import EventBus


def create_mock_keyboard():
    """Create a mock keyboard controller that supports context manager protocol."""
    mock = Mock(spec=keyboard.Controller)
    mock.pressed.return_value.__enter__ = Mock(return_value=None)
    mock.pressed.return_value.__exit__ = Mock(return_value=False)
    return mock


class TestCustomCommandInit(unittest.TestCase):
    """Test CustomCommand initialization."""

    def test_init(self):
        """Test custom command initialization."""
        cmd = CustomCommand(
            trigger="test command",
            action_type="type_text",
            action_data={"text": "Hello World"}
        )

        assert cmd.trigger == "test command"
        assert cmd.action_type == "type_text"
        assert cmd.action_data == {"text": "Hello World"}

    def test_init_strips_trigger(self):
        """Test trigger is stripped and lowercased."""
        cmd = CustomCommand(
            trigger="  TEST COMMAND  ",
            action_type="type_text",
            action_data={"text": "Hello"}
        )

        assert cmd.trigger == "test command"


class TestCustomCommandMatches(unittest.TestCase):
    """Test CustomCommand matching."""

    def test_matches_exact(self):
        """Test exact match."""
        cmd = CustomCommand(
            trigger="admin user",
            action_type="type_text",
            action_data={"text": "Administrator"}
        )

        assert cmd.matches("admin user") is True
        assert cmd.matches("ADMIN USER") is True
        assert cmd.matches("  admin user  ") is True

    def test_matches_no_match(self):
        """Test no match."""
        cmd = CustomCommand(
            trigger="admin user",
            action_type="type_text",
            action_data={"text": "Administrator"}
        )

        assert cmd.matches("admin") is False
        assert cmd.matches("user") is False
        assert cmd.matches("admin password") is False


class TestCustomCommandTypeText(unittest.TestCase):
    """Test type_text action."""

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

    def test_execute_type_text(self):
        """Test type_text action execution."""
        cmd = CustomCommand(
            trigger="admin user",
            action_type="type_text",
            action_data={"text": "Administrator"}
        )

        result = cmd.execute(self.context, "admin user")

        assert result is None
        self.mock_keyboard.type.assert_called_once_with("Administrator")

    def test_execute_type_text_empty(self):
        """Test type_text with empty text."""
        cmd = CustomCommand(
            trigger="test",
            action_type="type_text",
            action_data={}
        )

        result = cmd.execute(self.context, "test")

        assert result is None
        self.mock_keyboard.type.assert_not_called()


class TestCustomCommandCopyToClipboard(unittest.TestCase):
    """Test copy_to_clipboard action."""

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

    @patch('subprocess.run')
    @patch('os.name', 'nt')
    def test_execute_copy_to_clipboard_windows(self, mock_run):
        """Test copy_to_clipboard on Windows."""
        cmd = CustomCommand(
            trigger="copy admin",
            action_type="copy_to_clipboard",
            action_data={"text": "Administrator"}
        )

        result = cmd.execute(self.context, "copy admin")

        assert result is None
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == 'powershell'
        assert 'Administrator' in args[2]

    @patch('src.commands.handlers.custom_commands.pyperclip')
    @patch('os.name', 'posix')
    def test_execute_copy_to_clipboard_pyperclip(self, mock_pyperclip):
        """Test copy_to_clipboard with pyperclip."""
        cmd = CustomCommand(
            trigger="copy text",
            action_type="copy_to_clipboard",
            action_data={"text": "Test Text"}
        )

        result = cmd.execute(self.context, "copy text")

        assert result is None
        mock_pyperclip.copy.assert_called_once_with("Test Text")


class TestCustomCommandExecuteFile(unittest.TestCase):
    """Test execute_file action."""

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

    @patch('subprocess.Popen')
    @patch('os.path.exists', return_value=True)
    def test_execute_file(self, mock_exists, mock_popen):
        """Test execute_file action."""
        cmd = CustomCommand(
            trigger="run script",
            action_type="execute_file",
            action_data={"path": "/path/to/script.bat"}
        )

        result = cmd.execute(self.context, "run script")

        assert result is None
        mock_exists.assert_called_once()
        mock_popen.assert_called_once()

    @patch('os.path.exists', return_value=False)
    def test_execute_file_not_found(self, mock_exists):
        """Test execute_file with non-existent file."""
        cmd = CustomCommand(
            trigger="run script",
            action_type="execute_file",
            action_data={"path": "/path/to/missing.bat"}
        )

        result = cmd.execute(self.context, "run script")

        assert result is None
        mock_exists.assert_called_once()


class TestCustomCommandKeyCombination(unittest.TestCase):
    """Test key_combination action."""

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

    def test_execute_key_combination(self):
        """Test key_combination action."""
        cmd = CustomCommand(
            trigger="show desktop",
            action_type="key_combination",
            action_data={"keys": ["win", "d"]}
        )

        result = cmd.execute(self.context, "show desktop")

        assert result is None
        # Verify press was called for each key
        assert self.mock_keyboard.press.call_count == 2
        # Verify release was called for each key
        assert self.mock_keyboard.release.call_count == 2


class TestCustomCommandProperties(unittest.TestCase):
    """Test CustomCommand properties."""

    def test_priority(self):
        """Test custom command has high priority."""
        cmd = CustomCommand(
            trigger="test",
            action_type="type_text",
            action_data={"text": "test"}
        )
        assert cmd.priority == PRIORITY_HIGH

    def test_description_type_text(self):
        """Test description for type_text action."""
        cmd = CustomCommand(
            trigger="test",
            action_type="type_text",
            action_data={"text": "Hello World"}
        )
        assert cmd.description == "Type: Hello World"

    def test_description_type_text_truncated(self):
        """Test description for long type_text is truncated."""
        cmd = CustomCommand(
            trigger="test",
            action_type="type_text",
            action_data={"text": "A" * 50}
        )
        assert cmd.description == f"Type: {'A' * 27}..."

    def test_description_copy_to_clipboard(self):
        """Test description for copy_to_clipboard action."""
        cmd = CustomCommand(
            trigger="test",
            action_type="copy_to_clipboard",
            action_data={"text": "Test"}
        )
        assert cmd.description == "Copy: Test"

    def test_description_execute_file(self):
        """Test description for execute_file action."""
        cmd = CustomCommand(
            trigger="test",
            action_type="execute_file",
            action_data={"path": "/path/to/script.bat"}
        )
        assert cmd.description == "Run: script.bat"

    def test_description_key_combination(self):
        """Test description for key_combination action."""
        cmd = CustomCommand(
            trigger="test",
            action_type="key_combination",
            action_data={"keys": ["ctrl", "c"]}
        )
        assert cmd.description == "Press: ctrl+c"

    def test_examples(self):
        """Test examples property."""
        cmd = CustomCommand(
            trigger="admin user",
            action_type="type_text",
            action_data={"text": "Administrator"}
        )
        assert cmd.examples == ["admin user"]


class TestLoadCustomCommands(unittest.TestCase):
    """Test loading custom commands from config."""

    def test_load_custom_commands_disabled(self):
        """Test loading when custom commands are disabled."""
        config = Mock()
        config.get.return_value = False

        commands = load_custom_commands(config)

        assert commands == []

    def test_load_custom_commands_no_commands(self):
        """Test loading when no commands defined."""
        config = Mock()
        config.get.side_effect = [True, []]

        commands = load_custom_commands(config)

        assert commands == []

    def test_load_custom_commands_success(self):
        """Test loading custom commands successfully."""
        config = Mock()
        config.get.side_effect = [
            True,  # enabled
            [      # commands list
                {
                    "trigger": "admin user",
                    "action": {
                        "type": "type_text",
                        "text": "Administrator"
                    }
                }
            ]
        ]

        commands = load_custom_commands(config)

        assert len(commands) == 1
        assert commands[0].trigger == "admin user"
        assert commands[0].action_type == "type_text"

    def test_load_custom_commands_invalid_command(self):
        """Test loading with invalid command config."""
        config = Mock()
        config.get.side_effect = [
            True,  # enabled
            [      # commands list
                {
                    "trigger": "test"
                    # Missing action
                }
            ]
        ]

        commands = load_custom_commands(config)

        assert commands == []
