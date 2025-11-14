"""Unit tests for navigation command implementations."""

import os
import tempfile
import unittest
from unittest.mock import Mock

import yaml
from pynput import keyboard

from src.commands.handlers.navigation_commands import (
    ArrowKeyCommand,
    HomeEndCommand,
    PageNavigationCommand,
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


class TestArrowKeyCommand(unittest.TestCase):
    """Test cases for ArrowKeyCommand."""

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

    def test_arrow_key_matches(self):
        """Test arrow key command matching."""
        cmd = ArrowKeyCommand()
        self.assertTrue(cmd.matches("left"))
        self.assertTrue(cmd.matches("right"))
        self.assertTrue(cmd.matches("up"))
        self.assertTrue(cmd.matches("down"))
        self.assertTrue(cmd.matches("LEFT"))
        self.assertFalse(cmd.matches("move left"))
        self.assertFalse(cmd.matches("arrow left"))

    def test_arrow_key_left_execute(self):
        """Test left arrow key execution."""
        cmd = ArrowKeyCommand()
        result = cmd.execute(self.context, "left")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.left)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.left)

    def test_arrow_key_right_execute(self):
        """Test right arrow key execution."""
        cmd = ArrowKeyCommand()
        result = cmd.execute(self.context, "right")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.right)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.right)

    def test_arrow_key_up_execute(self):
        """Test up arrow key execution."""
        cmd = ArrowKeyCommand()
        result = cmd.execute(self.context, "up")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.up)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.up)

    def test_arrow_key_down_execute(self):
        """Test down arrow key execution."""
        cmd = ArrowKeyCommand()
        result = cmd.execute(self.context, "down")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.down)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.down)

    def test_arrow_key_priority(self):
        """Test arrow key command priority."""
        cmd = ArrowKeyCommand()
        self.assertEqual(cmd.priority, 150)

    def test_arrow_key_description(self):
        """Test arrow key command has description."""
        cmd = ArrowKeyCommand()
        self.assertIn("arrow", cmd.description.lower())

    def test_arrow_key_examples(self):
        """Test arrow key command provides examples."""
        cmd = ArrowKeyCommand()
        examples = cmd.examples
        self.assertIn("left", examples)
        self.assertIn("right", examples)
        self.assertIn("up", examples)
        self.assertIn("down", examples)


class TestPageNavigationCommand(unittest.TestCase):
    """Test cases for PageNavigationCommand."""

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

    def test_page_navigation_matches(self):
        """Test page navigation command matching."""
        cmd = PageNavigationCommand()
        self.assertTrue(cmd.matches("page up"))
        self.assertTrue(cmd.matches("page down"))
        self.assertTrue(cmd.matches("PAGE UP"))
        self.assertFalse(cmd.matches("page"))
        self.assertFalse(cmd.matches("up"))

    def test_page_up_execute(self):
        """Test page up execution."""
        cmd = PageNavigationCommand()
        result = cmd.execute(self.context, "page up")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.page_up)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.page_up)

    def test_page_down_execute(self):
        """Test page down execution."""
        cmd = PageNavigationCommand()
        result = cmd.execute(self.context, "page down")

        self.assertIsNone(result)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.page_down)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.page_down)

    def test_page_navigation_priority(self):
        """Test page navigation command priority."""
        cmd = PageNavigationCommand()
        self.assertEqual(cmd.priority, 200)

    def test_page_navigation_description(self):
        """Test page navigation command has description."""
        cmd = PageNavigationCommand()
        self.assertIn("page", cmd.description.lower())

    def test_page_navigation_examples(self):
        """Test page navigation command provides examples."""
        cmd = PageNavigationCommand()
        examples = cmd.examples
        self.assertIn("page up", examples)
        self.assertIn("page down", examples)


class TestHomeEndCommand(unittest.TestCase):
    """Test cases for HomeEndCommand."""

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

    def test_home_end_matches(self):
        """Test home/end command matching."""
        cmd = HomeEndCommand()
        self.assertTrue(cmd.matches("go to start"))
        self.assertTrue(cmd.matches("go to top"))
        self.assertTrue(cmd.matches("go to beginning"))
        self.assertTrue(cmd.matches("go to end"))
        self.assertTrue(cmd.matches("go to bottom"))
        self.assertTrue(cmd.matches("line start"))
        self.assertTrue(cmd.matches("line end"))
        self.assertFalse(cmd.matches("start"))
        self.assertFalse(cmd.matches("end"))

    def test_go_to_start_execute(self):
        """Test go to start execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "go to start")

        self.assertIsNone(result)
        # Should press Ctrl+Home
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.home)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.home)

    def test_go_to_top_execute(self):
        """Test go to top execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "go to top")

        self.assertIsNone(result)
        # Should press Ctrl+Home
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.home)

    def test_go_to_beginning_execute(self):
        """Test go to beginning execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "go to beginning")

        self.assertIsNone(result)
        # Should press Ctrl+Home
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.home)

    def test_go_to_end_execute(self):
        """Test go to end execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "go to end")

        self.assertIsNone(result)
        # Should press Ctrl+End
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.end)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.end)

    def test_go_to_bottom_execute(self):
        """Test go to bottom execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "go to bottom")

        self.assertIsNone(result)
        # Should press Ctrl+End
        self.mock_keyboard.pressed.assert_called_once_with(keyboard.Key.ctrl)
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.end)

    def test_line_start_execute(self):
        """Test line start execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "line start")

        self.assertIsNone(result)
        # Should press Home (without Ctrl)
        self.mock_keyboard.pressed.assert_not_called()
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.home)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.home)

    def test_line_end_execute(self):
        """Test line end execution."""
        cmd = HomeEndCommand()
        result = cmd.execute(self.context, "line end")

        self.assertIsNone(result)
        # Should press End (without Ctrl)
        self.mock_keyboard.pressed.assert_not_called()
        self.mock_keyboard.press.assert_called_once_with(keyboard.Key.end)
        self.mock_keyboard.release.assert_called_once_with(keyboard.Key.end)

    def test_home_end_priority(self):
        """Test home/end command priority."""
        cmd = HomeEndCommand()
        self.assertEqual(cmd.priority, 200)

    def test_home_end_description(self):
        """Test home/end command has description."""
        cmd = HomeEndCommand()
        self.assertIn("start", cmd.description.lower())
        self.assertIn("end", cmd.description.lower())

    def test_home_end_examples(self):
        """Test home/end command provides examples."""
        cmd = HomeEndCommand()
        examples = cmd.examples
        self.assertIn("go to start", examples)
        self.assertIn("go to end", examples)
        self.assertIn("line start", examples)
        self.assertIn("line end", examples)


class TestNavigationCommandPriorities(unittest.TestCase):
    """Test that navigation commands have appropriate priorities."""

    def test_command_priorities(self):
        """Test that navigation commands have correct priorities."""
        arrow_cmd = ArrowKeyCommand()
        page_cmd = PageNavigationCommand()
        home_end_cmd = HomeEndCommand()

        # Arrow keys should be 150 (basic)
        self.assertEqual(arrow_cmd.priority, 150)

        # Multi-word commands should be 200 (higher)
        self.assertEqual(page_cmd.priority, 200)
        self.assertEqual(home_end_cmd.priority, 200)

        # Multi-word should have higher priority than single word
        self.assertGreater(page_cmd.priority, arrow_cmd.priority)
        self.assertGreater(home_end_cmd.priority, arrow_cmd.priority)


class TestNavigationCommandDescriptions(unittest.TestCase):
    """Test that all navigation commands have proper documentation."""

    def test_all_commands_have_descriptions(self):
        """Test that all commands have descriptions."""
        commands = [
            ArrowKeyCommand(),
            PageNavigationCommand(),
            HomeEndCommand(),
        ]
        for cmd in commands:
            self.assertTrue(len(cmd.description) > 0, f"{cmd.__class__.__name__} has no description")

    def test_all_commands_have_examples(self):
        """Test that all commands have examples."""
        commands = [
            ArrowKeyCommand(),
            PageNavigationCommand(),
            HomeEndCommand(),
        ]
        for cmd in commands:
            self.assertTrue(len(cmd.examples) > 0, f"{cmd.__class__.__name__} has no examples")


if __name__ == '__main__':
    unittest.main()
