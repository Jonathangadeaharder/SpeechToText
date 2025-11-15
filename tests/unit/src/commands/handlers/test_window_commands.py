"""Unit tests for window command implementations."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml
from pynput import keyboard

from src.commands.handlers.window_commands import (
    CenterWindowCommand,
    CloseWindowCommand,
    MaximizeCommand,
    MinimizeCommand,
    MoveWindowCommand,
    SwitchWindowCommand,
)
from src.commands.base import CommandContext
from src.core.config import Config
from src.core.events import EventBus


def create_mock_keyboard():
    """Create a mock keyboard controller that supports context manager protocol."""
    mock = Mock(spec=keyboard.Controller)
    mock.pressed.return_value.__enter__ = Mock(return_value=None)
    mock.pressed.return_value.__exit__ = Mock(return_value=False)
    return mock


class TestMoveWindowCommand(unittest.TestCase):
    """Test cases for MoveWindowCommand."""

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

    def test_move_window_left_matches(self):
        """Test matching 'move window left' variants."""
        cmd = MoveWindowCommand()
        self.assertTrue(cmd.matches("move window left"))
        self.assertTrue(cmd.matches("MOVE WINDOW LEFT"))
        self.assertTrue(cmd.matches("snap left"))
        self.assertFalse(cmd.matches("move left"))
        self.assertFalse(cmd.matches("window left"))

    def test_move_window_right_matches(self):
        """Test matching 'move window right' variants."""
        cmd = MoveWindowCommand()
        self.assertTrue(cmd.matches("move window right"))
        self.assertTrue(cmd.matches("snap right"))
        self.assertFalse(cmd.matches("move right"))

    @patch('time.sleep')
    def test_move_window_left_execute(self, mock_sleep):
        """Test executing move window left."""
        cmd = MoveWindowCommand()
        result = cmd.execute(self.context, "move window left")

        self.assertIsNone(result)
        # Should press Win+Left
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.cmd)
        # Should press and release left key
        press_calls = [str(call) for call in self.mock_keyboard.press.call_args_list]
        self.assertTrue(any("Key.left" in call for call in press_calls))
        # Should press Enter to dismiss Snap Assist
        self.assertTrue(any("Key.enter" in call for call in press_calls))

    @patch('time.sleep')
    def test_move_window_right_execute(self, mock_sleep):
        """Test executing move window right."""
        cmd = MoveWindowCommand()
        result = cmd.execute(self.context, "move window right")

        self.assertIsNone(result)
        # Should press Win+Right
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.cmd)
        press_calls = [str(call) for call in self.mock_keyboard.press.call_args_list]
        self.assertTrue(any("Key.right" in call for call in press_calls))

    def test_move_window_priority(self):
        """Test move window command priority."""
        cmd = MoveWindowCommand()
        self.assertEqual(cmd.priority, 200)

    def test_move_window_description(self):
        """Test move window command has description."""
        cmd = MoveWindowCommand()
        self.assertIn("Snap", cmd.description)

    def test_move_window_examples(self):
        """Test move window command provides examples."""
        cmd = MoveWindowCommand()
        examples = cmd.examples
        self.assertIn("move window left", examples)
        self.assertIn("move window right", examples)


class TestMinimizeCommand(unittest.TestCase):
    """Test cases for MinimizeCommand."""

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

    def test_minimize_matches(self):
        """Test minimize command matching."""
        cmd = MinimizeCommand()
        self.assertTrue(cmd.matches("minimize"))
        self.assertTrue(cmd.matches("minimise"))
        self.assertTrue(cmd.matches("MINIMIZE"))
        self.assertFalse(cmd.matches("min"))

    @patch('platform.system')
    def test_minimize_execute_windows(self, mock_platform):
        """Test minimize on Windows."""
        mock_platform.return_value = "Windows"
        cmd = MinimizeCommand()
        result = cmd.execute(self.context, "minimize")

        self.assertIsNone(result)
        # Should press Win+Down
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.cmd)
        press_calls = [str(call) for call in self.mock_keyboard.press.call_args_list]
        self.assertTrue(any("Key.down" in call for call in press_calls))

    @patch('platform.system')
    def test_minimize_execute_other_platform(self, mock_platform):
        """Test minimize on non-Windows platform."""
        mock_platform.return_value = "Darwin"
        cmd = MinimizeCommand()
        result = cmd.execute(self.context, "minimize")

        self.assertIsNone(result)
        # Should press Cmd+M
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.cmd)
        self.mock_keyboard.press.assert_called_with("m")

    def test_minimize_priority(self):
        """Test minimize command priority."""
        cmd = MinimizeCommand()
        self.assertEqual(cmd.priority, 200)


class TestMaximizeCommand(unittest.TestCase):
    """Test cases for MaximizeCommand."""

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

    def test_maximize_matches(self):
        """Test maximize command matching."""
        cmd = MaximizeCommand()
        self.assertTrue(cmd.matches("maximize"))
        self.assertTrue(cmd.matches("maximise"))
        self.assertFalse(cmd.matches("max"))

    def test_maximize_execute(self):
        """Test maximize execution."""
        cmd = MaximizeCommand()
        result = cmd.execute(self.context, "maximize")

        self.assertIsNone(result)
        # Should press Win+Up
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.cmd)
        press_calls = [str(call) for call in self.mock_keyboard.press.call_args_list]
        self.assertTrue(any("Key.up" in call for call in press_calls))

    def test_maximize_priority(self):
        """Test maximize command priority."""
        cmd = MaximizeCommand()
        self.assertEqual(cmd.priority, 200)


class TestCloseWindowCommand(unittest.TestCase):
    """Test cases for CloseWindowCommand."""

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

    def test_close_window_matches(self):
        """Test close window command matching."""
        cmd = CloseWindowCommand()
        self.assertTrue(cmd.matches("close"))
        self.assertTrue(cmd.matches("close window"))
        self.assertFalse(cmd.matches("closing"))

    def test_close_window_execute(self):
        """Test close window execution."""
        cmd = CloseWindowCommand()
        result = cmd.execute(self.context, "close")

        self.assertIsNone(result)
        # Should press Alt+F4
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.alt)
        press_calls = [str(call) for call in self.mock_keyboard.press.call_args_list]
        self.assertTrue(any("Key.f4" in call for call in press_calls))

    def test_close_window_priority(self):
        """Test close window command priority."""
        cmd = CloseWindowCommand()
        self.assertEqual(cmd.priority, 200)


class TestSwitchWindowCommand(unittest.TestCase):
    """Test cases for SwitchWindowCommand."""

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

    def test_switch_window_matches(self):
        """Test switch window command matching."""
        cmd = SwitchWindowCommand()
        self.assertTrue(cmd.matches("switch"))
        self.assertTrue(cmd.matches("switch window"))
        self.assertTrue(cmd.matches("switch window previous"))
        self.assertFalse(cmd.matches("switching"))

    def test_switch_window_next_execute(self):
        """Test switch to next window."""
        cmd = SwitchWindowCommand()
        result = cmd.execute(self.context, "switch")

        self.assertIsNone(result)
        # Should press Alt+Tab
        self.mock_keyboard.pressed.assert_called_with(keyboard.Key.alt)
        press_calls = [str(call) for call in self.mock_keyboard.press.call_args_list]
        self.assertTrue(any("Key.tab" in call for call in press_calls))

    def test_switch_window_previous_execute(self):
        """Test switch to previous window."""
        cmd = SwitchWindowCommand()
        result = cmd.execute(self.context, "switch window previous")

        self.assertIsNone(result)
        # Should press Alt+Shift+Tab
        self.mock_keyboard.pressed.assert_called()
        # Check that both alt and shift pressed calls were made
        pressed_calls = [str(call) for call in self.mock_keyboard.pressed.call_args_list]
        self.assertTrue(any("Key.alt" in call for call in pressed_calls))
        self.assertTrue(any("Key.shift" in call for call in pressed_calls))

    def test_switch_window_priority(self):
        """Test switch window command priority."""
        cmd = SwitchWindowCommand()
        self.assertEqual(cmd.priority, 200)


class TestCenterWindowCommand(unittest.TestCase):
    """Test cases for CenterWindowCommand."""

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

    def test_center_window_matches(self):
        """Test center window command matching."""
        cmd = CenterWindowCommand()
        self.assertTrue(cmd.matches("center window"))
        self.assertTrue(cmd.matches("centre window"))
        self.assertFalse(cmd.matches("center"))

    def test_center_window_execute(self):
        """Test center window execution (placeholder)."""
        cmd = CenterWindowCommand()
        result = cmd.execute(self.context, "center window")

        # Placeholder implementation returns None
        self.assertIsNone(result)

    def test_center_window_priority(self):
        """Test center window command priority."""
        cmd = CenterWindowCommand()
        self.assertEqual(cmd.priority, 200)


class TestWindowCommandPriorities(unittest.TestCase):
    """Test that all window commands have appropriate priorities."""

    def test_all_commands_have_priority_200(self):
        """Test that all window commands use priority 200."""
        commands = [
            MoveWindowCommand(),
            MinimizeCommand(),
            MaximizeCommand(),
            CloseWindowCommand(),
            SwitchWindowCommand(),
            CenterWindowCommand(),
        ]
        for cmd in commands:
            self.assertEqual(cmd.priority, 200, f"{cmd.__class__.__name__} has wrong priority")


class TestWindowCommandDescriptions(unittest.TestCase):
    """Test that all window commands have proper documentation."""

    def test_all_commands_have_descriptions(self):
        """Test that all commands have descriptions."""
        commands = [
            MoveWindowCommand(),
            MinimizeCommand(),
            MaximizeCommand(),
            CloseWindowCommand(),
            SwitchWindowCommand(),
            CenterWindowCommand(),
        ]
        for cmd in commands:
            self.assertTrue(len(cmd.description) > 0, f"{cmd.__class__.__name__} has no description")

    def test_all_commands_have_examples(self):
        """Test that all commands have examples."""
        commands = [
            MoveWindowCommand(),
            MinimizeCommand(),
            MaximizeCommand(),
            CloseWindowCommand(),
            SwitchWindowCommand(),
            CenterWindowCommand(),
        ]
        for cmd in commands:
            self.assertTrue(len(cmd.examples) > 0, f"{cmd.__class__.__name__} has no examples")


if __name__ == '__main__':
    unittest.main()
