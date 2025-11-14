"""Unit tests for the Config class."""

import os
import tempfile
import unittest

import yaml

from src.core.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""

    def test_default_config_creation(self):
        """Test that default config is created when file doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            config_path = tf.name + "_nonexistent.yaml"

        try:
            config = Config(config_path)

            # Check that default values are present
            self.assertEqual(config.get("audio", "sample_rate"), 16000)
            self.assertEqual(config.get("audio", "channels"), 1)
            self.assertIsNotNone(config.get("model", "name"))
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_config_get_nested(self):
        """Test nested config value retrieval."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump({
                "test": {
                    "nested": {
                        "value": 42
                    }
                }
            }, tf)
            config_path = tf.name

        try:
            config = Config(config_path)

            # Test nested access
            self.assertEqual(config.get("test", "nested", "value"), 42)

            # Test default value
            self.assertEqual(config.get("test", "missing", default=99), 99)

            # Test missing key returns default
            self.assertIsNone(config.get("nonexistent", "key"))
        finally:
            os.remove(config_path)

    def test_config_get_with_default(self):
        """Test that default value is returned for missing keys."""
        config = Config()

        # Test missing key with default
        result = config.get("missing", "key", default="default_value")
        self.assertEqual(result, "default_value")

    def test_hotkeys_configuration(self):
        """Test hotkey configuration loading."""
        config = Config()

        push_to_talk = config.get("hotkeys", "push_to_talk")
        self.assertIsInstance(push_to_talk, list)
        self.assertGreater(len(push_to_talk), 0)


if __name__ == '__main__':
    unittest.main()
