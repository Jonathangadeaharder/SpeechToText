"""Configuration management for the dictation tool."""

import logging
import os
from typing import Any, Dict, Optional

import yaml


class ConfigLoader:
    """
    Handles loading configuration from files.

    Single Responsibility Principle: Only responsible for loading/reading config data.
    """

    @staticmethod
    def load_from_file(config_path: str) -> Optional[Dict]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Configuration dictionary, or None if loading failed
        """
        if not os.path.exists(config_path):
            logging.warning(f"Config file not found at {config_path}")
            return None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logging.info(f"Configuration loaded from {config_path}")
            return config
        except (OSError, IOError) as e:
            logging.exception(f"Error reading config file {config_path}: {e}")
            return None
        except yaml.YAMLError as e:
            logging.exception(f"Error parsing YAML config {config_path}: {e}")
            return None

    @staticmethod
    def get_default_config() -> Dict:
        """Return default configuration."""
        return {
            "hotkeys": {
                "push_to_talk": ["ctrl", "cmd"],
                "toggle_continuous": ["ctrl", "shift", "d"],
            },
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024,
                "beep_on_start": True,
                "beep_on_stop": True,
                "start_beep_frequency": 800,
                "start_beep_duration": 100,
                "stop_beep_frequency": 600,
                "stop_beep_duration": 100,
            },
            "model": {
                "name": "small.en",
                "device": "auto",
                "compute_type": "int8",
                "beam_size": 5,
                "language": "en",
            },
            "text_processing": {
                "punctuation_commands": True,
                "punctuation_map": {
                    "period": ".",
                    "comma": ",",
                    "question mark": "?",
                    "exclamation point": "!",
                    "new line": "\n",
                    "new paragraph": "\n\n",
                },
                "custom_vocabulary": {},
                "command_words": {
                    "delete that": "undo_last",
                    "scratch that": "undo_last",
                },
            },
            "continuous_mode": {
                "enabled": False,
                "silence_threshold": 2.0,
                "minimum_audio_length": 0.5,
            },
            "system_tray": {
                "enabled": True,
                "show_notifications": True,
                "notification_duration": 2,
            },
            "wake_word": {"enabled": False, "word": "hey computer", "sensitivity": 0.5},
            "advanced": {
                "log_level": "INFO",
                "verbose": False,
                "max_recording_duration": 60,
                "transcription_threads": 1,
            },
        }


class LoggingConfigurator:
    """
    Handles logging configuration setup.

    Single Responsibility Principle: Only responsible for configuring logging.
    """

    @staticmethod
    def setup_logging(config: Dict) -> None:
        """
        Setup logging based on configuration.

        Args:
            config: Configuration dictionary
        """
        log_level = getattr(
            logging,
            config.get("advanced", {}).get("log_level", "INFO"),
            logging.INFO
        )
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


class Config:
    """
    Configuration manager for the dictation tool.

    Single Responsibility Principle: Provides unified access to configuration values.
    Delegates loading to ConfigLoader and logging setup to LoggingConfigurator.
    """

    def __init__(self, config_path: str = "config.yaml", setup_logging: bool = True):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file
            setup_logging: Whether to setup logging (default True)
        """
        self.config_path = config_path
        self.config = self._load_config()
        if setup_logging:
            LoggingConfigurator.setup_logging(self.config)

    def _load_config(self) -> Dict:
        """
        Load configuration using ConfigLoader.

        Returns:
            Configuration dictionary
        """
        config = ConfigLoader.load_from_file(self.config_path)
        if config is None:
            logging.info("Using default configuration...")
            config = ConfigLoader.get_default_config()
        return config

    def get(self, *keys, default=None) -> Any:
        """
        Get a nested configuration value.

        Args:
            *keys: Sequence of keys to navigate nested dict
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            config.get("audio", "sample_rate", default=16000)
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
