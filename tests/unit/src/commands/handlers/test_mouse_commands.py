"""Unit tests for mouse command implementations."""

import os
import tempfile
import unittest
from unittest.mock import Mock, MagicMock

import yaml
from pynput import mouse

from src.commands.handlers.mouse_commands import (
    ClickCommand,
    ClickNumberCommand,
    DoubleClickCommand,
    MiddleClickCommand,
    MouseMoveCommand,
    RightClickCommand,
    ScrollCommand,
)
from src.commands.base import CommandContext
from src.commands.parser import CommandParser
from src.core.config import Config
from src.core.events import EventBus


class TestClickCommands(unittest.TestCase):
    """Test cases for click commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock(spec=mouse.Controller)
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

    def test_click_command_matches(self):
        """Test left click command matching."""
        cmd = ClickCommand()
        self.assertTrue(cmd.matches("click"))
        self.assertTrue(cmd.matches("CLICK"))
        self.assertTrue(cmd.matches("  click  "))
        self.assertFalse(cmd.matches("click 5"))
        self.assertFalse(cmd.matches("double click"))

    def test_click_command_execute(self):
        """Test left click execution."""
        cmd = ClickCommand()
        result = cmd.execute(self.context, "click")

        self.assertIsNone(result)
        self.mock_mouse.click.assert_called_once_with(mouse.Button.left, 1)

    def test_right_click_command_matches(self):
        """Test right click command matching."""
        cmd = RightClickCommand()
        self.assertTrue(cmd.matches("right click"))
        self.assertTrue(cmd.matches("RIGHT CLICK"))
        self.assertFalse(cmd.matches("click"))

    def test_right_click_command_execute(self):
        """Test right click execution."""
        cmd = RightClickCommand()
        result = cmd.execute(self.context, "right click")

        self.assertIsNone(result)
        self.mock_mouse.click.assert_called_once_with(mouse.Button.right, 1)

    def test_double_click_command_matches(self):
        """Test double click command matching."""
        cmd = DoubleClickCommand()
        self.assertTrue(cmd.matches("double click"))
        self.assertTrue(cmd.matches("DOUBLE CLICK"))
        self.assertFalse(cmd.matches("click"))

    def test_double_click_command_execute(self):
        """Test double click execution."""
        cmd = DoubleClickCommand()
        result = cmd.execute(self.context, "double click")

        self.assertIsNone(result)
        self.mock_mouse.click.assert_called_once_with(mouse.Button.left, 2)

    def test_middle_click_command_matches(self):
        """Test middle click command matching."""
        cmd = MiddleClickCommand()
        self.assertTrue(cmd.matches("middle click"))
        self.assertTrue(cmd.matches("wheel click"))
        self.assertFalse(cmd.matches("click"))

    def test_middle_click_command_execute(self):
        """Test middle click execution."""
        cmd = MiddleClickCommand()
        result = cmd.execute(self.context, "middle click")

        self.assertIsNone(result)
        self.mock_mouse.click.assert_called_once_with(mouse.Button.middle, 1)

    def test_click_command_priorities(self):
        """Test that specialized clicks have higher priority."""
        self.assertEqual(ClickCommand().priority, 100)
        self.assertEqual(RightClickCommand().priority, 200)
        self.assertEqual(DoubleClickCommand().priority, 200)
        self.assertEqual(MiddleClickCommand().priority, 200)


class TestScrollCommand(unittest.TestCase):
    """Test cases for scroll command."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock(spec=mouse.Controller)

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_scroll_command_matches(self):
        """Test scroll command matching."""
        cmd = ScrollCommand()
        self.assertTrue(cmd.matches("scroll up"))
        self.assertTrue(cmd.matches("scroll down"))
        self.assertTrue(cmd.matches("scroll left"))
        self.assertTrue(cmd.matches("scroll right"))
        self.assertFalse(cmd.matches("scroll"))
        self.assertFalse(cmd.matches("move up"))

    def test_scroll_up_execute(self):
        """Test scroll up execution."""
        cmd = ScrollCommand()
        result = cmd.execute(self.context, "scroll up")

        self.assertIsNone(result)
        self.mock_mouse.scroll.assert_called_once_with(0, -3)

    def test_scroll_down_execute(self):
        """Test scroll down execution."""
        cmd = ScrollCommand()
        result = cmd.execute(self.context, "scroll down")

        self.assertIsNone(result)
        self.mock_mouse.scroll.assert_called_once_with(0, 3)

    def test_scroll_left_execute(self):
        """Test scroll left execution."""
        cmd = ScrollCommand()
        result = cmd.execute(self.context, "scroll left")

        self.assertIsNone(result)
        self.mock_mouse.scroll.assert_called_once_with(-3, 0)

    def test_scroll_right_execute(self):
        """Test scroll right execution."""
        cmd = ScrollCommand()
        result = cmd.execute(self.context, "scroll right")

        self.assertIsNone(result)
        self.mock_mouse.scroll.assert_called_once_with(3, 0)

    def test_scroll_exponential_scaling(self):
        """Test scroll exponential scaling on repeated commands."""
        cmd = ScrollCommand()

        # First scroll
        cmd.execute(self.context, "scroll up")
        self.mock_mouse.scroll.assert_called_with(0, -3)  # Base amount

        # Second scroll (same direction)
        cmd.execute(self.context, "scroll up")
        self.mock_mouse.scroll.assert_called_with(0, -6)  # 2x

        # Third scroll (same direction)
        cmd.execute(self.context, "scroll up")
        self.mock_mouse.scroll.assert_called_with(0, -12)  # 4x

    def test_scroll_reset_on_direction_change(self):
        """Test scroll multiplier resets when direction changes."""
        cmd = ScrollCommand()

        # First scroll up
        cmd.execute(self.context, "scroll up")
        self.mock_mouse.scroll.assert_called_with(0, -3)

        # Second scroll up (2x)
        cmd.execute(self.context, "scroll up")
        self.mock_mouse.scroll.assert_called_with(0, -6)

        # Change direction to down (should reset)
        cmd.execute(self.context, "scroll down")
        self.mock_mouse.scroll.assert_called_with(0, 3)  # Back to base


class TestMouseMoveCommand(unittest.TestCase):
    """Test cases for mouse move command."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock(spec=mouse.Controller)
        # Set initial position
        self.mock_mouse.position = (500, 500)

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            screen_width=1920,
            screen_height=1080,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_mouse_move_command_matches(self):
        """Test mouse move command matching."""
        cmd = MouseMoveCommand()
        self.assertTrue(cmd.matches("move up"))
        self.assertTrue(cmd.matches("move down"))
        self.assertFalse(cmd.matches("move left"))  # Window command
        self.assertFalse(cmd.matches("move right"))  # Window command
        self.assertFalse(cmd.matches("scroll up"))

    def test_mouse_move_up_execute(self):
        """Test mouse move up execution."""
        cmd = MouseMoveCommand()
        result = cmd.execute(self.context, "move up")

        self.assertIsNone(result)
        # Should move up by base step (50px)
        expected_y = 500 - 50  # 450
        self.mock_mouse.position = (500, expected_y)

    def test_mouse_move_down_execute(self):
        """Test mouse move down execution."""
        cmd = MouseMoveCommand()
        result = cmd.execute(self.context, "move down")

        self.assertIsNone(result)
        # Should move down by base step (50px)
        expected_y = 500 + 50  # 550
        self.mock_mouse.position = (500, expected_y)

    def test_mouse_move_exponential_scaling(self):
        """Test mouse move exponential scaling on repeated commands."""
        cmd = MouseMoveCommand()

        # First move
        cmd.execute(self.context, "move up")
        # Base step = 50px

        # Second move (same direction)
        cmd.execute(self.context, "move up")
        # Should be 100px (2x)

        # Third move (same direction)
        cmd.execute(self.context, "move up")
        # Should be 200px (4x)

    def test_mouse_move_capped_at_800(self):
        """Test mouse move is capped at 800px."""
        cmd = MouseMoveCommand()

        # Execute many times to hit the cap
        for _ in range(10):
            cmd.execute(self.context, "move up")

        # Should be capped at 800px per move


class TestClickNumberCommand(unittest.TestCase):
    """Test cases for click number command."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock(spec=mouse.Controller)
        self.parser = CommandParser()
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

    def test_click_number_command_matches(self):
        """Test click number command matching."""
        cmd = ClickNumberCommand(self.parser)
        self.assertTrue(cmd.matches("click 5"))
        self.assertTrue(cmd.matches("click number 12"))
        self.assertTrue(cmd.matches("click two"))
        self.assertFalse(cmd.matches("click"))
        self.assertFalse(cmd.matches("right click"))

    def test_click_number_command_extract_digit(self):
        """Test extracting digit number."""
        cmd = ClickNumberCommand(self.parser)

        # Execute and verify event published
        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe("COMMAND_EXECUTED", callback)

        result = cmd.execute(self.context, "click 5")
        self.assertIsNone(result)

    def test_click_number_command_extract_word(self):
        """Test extracting word number."""
        cmd = ClickNumberCommand(self.parser)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe("COMMAND_EXECUTED", callback)

        result = cmd.execute(self.context, "click five")
        self.assertIsNone(result)

    def test_click_number_command_extract_homophone(self):
        """Test extracting homophone number."""
        cmd = ClickNumberCommand(self.parser)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe("COMMAND_EXECUTED", callback)

        result = cmd.execute(self.context, "click to")  # "to" -> 2
        self.assertIsNone(result)

    def test_click_number_command_priority(self):
        """Test click number has high priority."""
        cmd = ClickNumberCommand(self.parser)
        self.assertEqual(cmd.priority, 500)


if __name__ == '__main__':
    unittest.main()
