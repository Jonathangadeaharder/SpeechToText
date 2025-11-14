"""Unit tests for overlay command implementations."""

import os
import tempfile
import unittest
from unittest.mock import Mock

import yaml

from src.commands.handlers.overlay_commands import (
    HideOverlayCommand,
    ShowElementsCommand,
    ShowGridCommand,
    ShowHelpCommand,
    ShowWindowsCommand,
)
from src.commands.base import CommandContext
from src.core.config import Config
from src.core.events import EventBus


class TestShowGridCommand(unittest.TestCase):
    """Test cases for ShowGridCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock()
        self.mock_overlay = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=self.mock_overlay,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_show_grid_matches(self):
        """Test show grid command matching."""
        cmd = ShowGridCommand()
        self.assertTrue(cmd.matches("grid"))
        self.assertTrue(cmd.matches("GRID"))
        self.assertFalse(cmd.matches("show grid"))
        self.assertFalse(cmd.matches("grid overlay"))

    def test_show_grid_execute(self):
        """Test show grid execution."""
        cmd = ShowGridCommand()
        result = cmd.execute(self.context, "grid")

        self.assertIsNone(result)
        self.mock_overlay.show_grid.assert_called_once_with(subdivisions=9)

    def test_show_grid_no_overlay_manager(self):
        """Test show grid when overlay manager is None."""
        context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=None,
        )
        cmd = ShowGridCommand()
        result = cmd.execute(context, "grid")

        self.assertIsNone(result)

    def test_show_grid_priority(self):
        """Test show grid command priority."""
        cmd = ShowGridCommand()
        self.assertEqual(cmd.priority, 200)

    def test_show_grid_description(self):
        """Test show grid command has description."""
        cmd = ShowGridCommand()
        self.assertIn("grid", cmd.description.lower())

    def test_show_grid_examples(self):
        """Test show grid command provides examples."""
        cmd = ShowGridCommand()
        examples = cmd.examples
        self.assertIn("grid", examples)


class TestShowElementsCommand(unittest.TestCase):
    """Test cases for ShowElementsCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock()
        self.mock_overlay = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=self.mock_overlay,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_show_elements_matches(self):
        """Test show elements command matching."""
        cmd = ShowElementsCommand()
        self.assertTrue(cmd.matches("numbers"))
        self.assertTrue(cmd.matches("show numbers"))
        self.assertTrue(cmd.matches("show elements"))
        self.assertTrue(cmd.matches("NUMBERS"))
        self.assertFalse(cmd.matches("number"))

    def test_show_elements_execute(self):
        """Test show elements execution."""
        cmd = ShowElementsCommand()
        result = cmd.execute(self.context, "numbers")

        self.assertIsNone(result)
        self.mock_overlay.show_numbers.assert_called_once()

    def test_show_elements_no_overlay_manager(self):
        """Test show elements when overlay manager is None."""
        context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=None,
        )
        cmd = ShowElementsCommand()
        result = cmd.execute(context, "numbers")

        self.assertIsNone(result)

    def test_show_elements_priority(self):
        """Test show elements command priority."""
        cmd = ShowElementsCommand()
        self.assertEqual(cmd.priority, 200)

    def test_show_elements_description(self):
        """Test show elements command has description."""
        cmd = ShowElementsCommand()
        self.assertIn("element", cmd.description.lower())

    def test_show_elements_examples(self):
        """Test show elements command provides examples."""
        cmd = ShowElementsCommand()
        examples = cmd.examples
        self.assertIn("numbers", examples)
        self.assertIn("show numbers", examples)


class TestShowWindowsCommand(unittest.TestCase):
    """Test cases for ShowWindowsCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock()
        self.mock_overlay = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=self.mock_overlay,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_show_windows_matches(self):
        """Test show windows command matching."""
        cmd = ShowWindowsCommand()
        self.assertTrue(cmd.matches("windows"))
        self.assertTrue(cmd.matches("show windows"))
        self.assertTrue(cmd.matches("list windows"))
        self.assertTrue(cmd.matches("WINDOWS"))
        self.assertFalse(cmd.matches("window"))

    def test_show_windows_execute(self):
        """Test show windows execution."""
        cmd = ShowWindowsCommand()
        result = cmd.execute(self.context, "windows")

        self.assertIsNone(result)
        self.mock_overlay.show_windows.assert_called_once()

    def test_show_windows_no_overlay_manager(self):
        """Test show windows when overlay manager is None."""
        context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=None,
        )
        cmd = ShowWindowsCommand()
        result = cmd.execute(context, "windows")

        self.assertIsNone(result)

    def test_show_windows_priority(self):
        """Test show windows command priority."""
        cmd = ShowWindowsCommand()
        self.assertEqual(cmd.priority, 200)

    def test_show_windows_description(self):
        """Test show windows command has description."""
        cmd = ShowWindowsCommand()
        self.assertIn("windows", cmd.description.lower())

    def test_show_windows_examples(self):
        """Test show windows command provides examples."""
        cmd = ShowWindowsCommand()
        examples = cmd.examples
        self.assertIn("windows", examples)
        self.assertIn("show windows", examples)


class TestHideOverlayCommand(unittest.TestCase):
    """Test cases for HideOverlayCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock()
        self.mock_overlay = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=self.mock_overlay,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_hide_overlay_matches_basic(self):
        """Test basic hide overlay command matching."""
        cmd = HideOverlayCommand()
        self.assertTrue(cmd.matches("hide numbers"))
        self.assertTrue(cmd.matches("hide grid"))
        self.assertTrue(cmd.matches("hide windows"))
        self.assertTrue(cmd.matches("hide overlay"))
        self.assertTrue(cmd.matches("close overlay"))

    def test_hide_overlay_matches_misrecognitions(self):
        """Test matching common speech recognition errors."""
        cmd = HideOverlayCommand()
        # "hide" often transcribed as "height"
        self.assertTrue(cmd.matches("height numbers"))
        self.assertTrue(cmd.matches("height grid"))
        self.assertTrue(cmd.matches("height windows"))
        self.assertTrue(cmd.matches("height overlay"))

    def test_hide_overlay_matches_rows_variants(self):
        """Test matching 'rows' and its misrecognitions."""
        cmd = HideOverlayCommand()
        self.assertTrue(cmd.matches("hide rows"))
        self.assertTrue(cmd.matches("hide rose"))  # "rows" -> "rose"
        self.assertTrue(cmd.matches("hide roles"))  # "rows" -> "roles"
        self.assertTrue(cmd.matches("close rows"))
        self.assertTrue(cmd.matches("close rose"))
        self.assertTrue(cmd.matches("close roles"))

    def test_hide_overlay_matches_commands_help(self):
        """Test matching hide commands/help variants."""
        cmd = HideOverlayCommand()
        self.assertTrue(cmd.matches("hide commands"))
        self.assertTrue(cmd.matches("hide help"))
        self.assertTrue(cmd.matches("close commands"))
        self.assertTrue(cmd.matches("close help"))
        self.assertTrue(cmd.matches("height commands"))
        self.assertTrue(cmd.matches("height help"))

    def test_hide_overlay_matches_other_variants(self):
        """Test matching other hide variants."""
        cmd = HideOverlayCommand()
        self.assertTrue(cmd.matches("remove overlay"))
        self.assertTrue(cmd.matches("clear overlay"))

    def test_hide_overlay_execute(self):
        """Test hide overlay execution."""
        cmd = HideOverlayCommand()
        result = cmd.execute(self.context, "hide numbers")

        self.assertIsNone(result)
        self.mock_overlay.hide.assert_called_once()

    def test_hide_overlay_no_overlay_manager(self):
        """Test hide overlay when overlay manager is None."""
        context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=None,
        )
        cmd = HideOverlayCommand()
        result = cmd.execute(context, "hide numbers")

        self.assertIsNone(result)

    def test_hide_overlay_priority(self):
        """Test hide overlay command priority."""
        cmd = HideOverlayCommand()
        self.assertEqual(cmd.priority, 200)

    def test_hide_overlay_description(self):
        """Test hide overlay command has description."""
        cmd = HideOverlayCommand()
        self.assertIn("hide", cmd.description.lower())

    def test_hide_overlay_examples(self):
        """Test hide overlay command provides examples."""
        cmd = HideOverlayCommand()
        examples = cmd.examples
        self.assertIn("hide numbers", examples)
        self.assertIn("hide grid", examples)


class TestShowHelpCommand(unittest.TestCase):
    """Test cases for ShowHelpCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_data = {"advanced": {"log_level": "INFO"}}
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.mock_keyboard = Mock()
        self.mock_mouse = Mock()
        self.mock_overlay = Mock()
        self.event_bus = EventBus()

        self.context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=self.mock_overlay,
            event_bus=self.event_bus,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_show_help_matches(self):
        """Test show help command matching."""
        cmd = ShowHelpCommand()
        self.assertTrue(cmd.matches("commands"))
        self.assertTrue(cmd.matches("show commands"))
        self.assertTrue(cmd.matches("help"))
        self.assertTrue(cmd.matches("show help"))
        self.assertTrue(cmd.matches("HELP"))
        self.assertFalse(cmd.matches("command"))

    def test_show_help_execute(self):
        """Test show help execution."""
        cmd = ShowHelpCommand()
        result = cmd.execute(self.context, "help")

        self.assertIsNone(result)
        self.mock_overlay.show_commands.assert_called_once()

    def test_show_help_no_overlay_manager(self):
        """Test show help when overlay manager is None."""
        context = CommandContext(
            config=self.config,
            keyboard_controller=self.mock_keyboard,
            mouse_controller=self.mock_mouse,
            overlay_manager=None,
        )
        cmd = ShowHelpCommand()
        result = cmd.execute(context, "help")

        self.assertIsNone(result)

    def test_show_help_priority(self):
        """Test show help command priority."""
        cmd = ShowHelpCommand()
        self.assertEqual(cmd.priority, 200)

    def test_show_help_description(self):
        """Test show help command has description."""
        cmd = ShowHelpCommand()
        self.assertIn("help", cmd.description.lower())

    def test_show_help_examples(self):
        """Test show help command provides examples."""
        cmd = ShowHelpCommand()
        examples = cmd.examples
        self.assertIn("help", examples)
        self.assertIn("commands", examples)


class TestOverlayCommandPriorities(unittest.TestCase):
    """Test that all overlay commands have appropriate priorities."""

    def test_all_commands_have_priority_200(self):
        """Test that all overlay commands use priority 200."""
        commands = [
            ShowGridCommand(),
            ShowElementsCommand(),
            ShowWindowsCommand(),
            HideOverlayCommand(),
            ShowHelpCommand(),
        ]
        for cmd in commands:
            self.assertEqual(cmd.priority, 200, f"{cmd.__class__.__name__} has wrong priority")


class TestOverlayCommandDescriptions(unittest.TestCase):
    """Test that all overlay commands have proper documentation."""

    def test_all_commands_have_descriptions(self):
        """Test that all commands have descriptions."""
        commands = [
            ShowGridCommand(),
            ShowElementsCommand(),
            ShowWindowsCommand(),
            HideOverlayCommand(),
            ShowHelpCommand(),
        ]
        for cmd in commands:
            self.assertTrue(len(cmd.description) > 0, f"{cmd.__class__.__name__} has no description")

    def test_all_commands_have_examples(self):
        """Test that all commands have examples."""
        commands = [
            ShowGridCommand(),
            ShowElementsCommand(),
            ShowWindowsCommand(),
            HideOverlayCommand(),
            ShowHelpCommand(),
        ]
        for cmd in commands:
            self.assertTrue(len(cmd.examples) > 0, f"{cmd.__class__.__name__} has no examples")


if __name__ == '__main__':
    unittest.main()
