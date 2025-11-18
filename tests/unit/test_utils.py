"""Shared test utilities for command and overlay tests."""

import os
import tempfile
import unittest
from unittest.mock import Mock

import yaml
from pynput import keyboard

from src.commands.base import CommandContext
from src.core.config import Config
from src.core.events import EventBus


def create_mock_keyboard():
    """Create a mock keyboard controller that supports context manager protocol."""
    mock = Mock(spec=keyboard.Controller)
    # Configure the mock to support context manager protocol
    mock.pressed.return_value.__enter__ = Mock(return_value=None)
    mock.pressed.return_value.__exit__ = Mock(return_value=False)
    return mock


class BaseCommandTest(unittest.TestCase):
    """Base test class for command tests with common setup and teardown."""

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
