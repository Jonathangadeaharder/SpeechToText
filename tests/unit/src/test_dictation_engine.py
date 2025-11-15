"""Unit tests for DictationEngine."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from src.dictation_engine import DictationEngine


class TestDictationEngine(unittest.TestCase):
    """Test cases for DictationEngine class."""

    @patch('src.dictation_engine.WhisperModel')
    @patch('src.dictation_engine.pyaudio.PyAudio')
    def setUp(self, mock_pyaudio, mock_whisper):
        """Set up test fixtures with mocked dependencies."""
        # Mock the Whisper model
        self.mock_model = Mock()
        mock_whisper.return_value = self.mock_model

        # Mock PyAudio
        self.mock_audio = Mock()
        mock_pyaudio.return_value = self.mock_audio

        # Create mock dependencies
        self.mock_config = Mock()
        self.mock_config.get.return_value = 16000
        self.mock_event_bus = Mock()
        self.mock_event_bus.publish = Mock()
        self.mock_event_bus.subscribe = Mock()
        self.mock_registry = Mock()
        self.mock_registry.register = Mock()
        self.mock_registry.execute = Mock()
        self.mock_text_processor = Mock()
        self.mock_parser = Mock()

        # Create DictationEngine instance with mocked dependencies
        self.engine = DictationEngine(
            config=self.mock_config,
            event_bus=self.mock_event_bus,
            command_registry=self.mock_registry,
            text_processor=self.mock_text_processor,
            parser=self.mock_parser
        )

    def test_initialization(self):
        """Test that DictationEngine initializes correctly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.config)
        self.assertIsNotNone(self.engine.event_bus)
        self.assertIsNotNone(self.engine.command_registry)
        self.assertIsNotNone(self.engine.parser)

    @patch('src.dictation_engine.WhisperModel')
    @patch('src.dictation_engine.pyaudio.PyAudio')
    def test_config_loading(self, mock_pyaudio, mock_whisper):
        """Test that configuration is properly loaded."""
        mock_config = Mock()
        mock_config.get.return_value = 16000
        mock_event_bus = Mock()
        mock_registry = Mock()
        mock_text_processor = Mock()
        mock_parser = Mock()

        engine = DictationEngine(
            config=mock_config,
            event_bus=mock_event_bus,
            command_registry=mock_registry,
            text_processor=mock_text_processor,
            parser=mock_parser
        )

        # Verify config was accessed
        self.assertIsNotNone(engine.config)
        self.assertEqual(engine.config, mock_config)

    @patch('src.dictation_engine.WhisperModel')
    @patch('src.dictation_engine.pyaudio.PyAudio')
    def test_event_bus_initialization(self, mock_pyaudio, mock_whisper):
        """Test that event bus is properly initialized."""
        mock_config = Mock()
        mock_config.get.return_value = 16000
        mock_event_bus = Mock()
        mock_event_bus.publish = Mock()
        mock_event_bus.subscribe = Mock()
        mock_registry = Mock()
        mock_text_processor = Mock()
        mock_parser = Mock()

        engine = DictationEngine(
            config=mock_config,
            event_bus=mock_event_bus,
            command_registry=mock_registry,
            text_processor=mock_text_processor,
            parser=mock_parser
        )

        self.assertIsNotNone(engine.event_bus)
        self.assertTrue(hasattr(engine.event_bus, 'publish'))
        self.assertTrue(hasattr(engine.event_bus, 'subscribe'))

    @patch('src.dictation_engine.WhisperModel')
    @patch('src.dictation_engine.pyaudio.PyAudio')
    def test_command_registry_initialization(self, mock_pyaudio, mock_whisper):
        """Test that command registry is properly initialized."""
        mock_config = Mock()
        mock_config.get.return_value = 16000
        mock_event_bus = Mock()
        mock_registry = Mock()
        mock_registry.register = Mock()
        mock_registry.execute = Mock()
        mock_text_processor = Mock()
        mock_parser = Mock()

        engine = DictationEngine(
            config=mock_config,
            event_bus=mock_event_bus,
            command_registry=mock_registry,
            text_processor=mock_text_processor,
            parser=mock_parser
        )

        self.assertIsNotNone(engine.command_registry)
        self.assertTrue(hasattr(engine.command_registry, 'register'))
        self.assertTrue(hasattr(engine.command_registry, 'execute'))

    def test_check_silence(self):
        """Test check_silence method."""
        # Mock VAD to return specific silence duration
        self.engine.vad.get_silence_duration = Mock(return_value=3.0)

        # Test with threshold below silence duration
        self.assertTrue(self.engine.check_silence(2.0))

        # Test with threshold above silence duration
        self.assertFalse(self.engine.check_silence(4.0))

    def test_has_speech(self):
        """Test has_speech method."""
        # Initially no speech detected
        self.engine.vad.speech_detected = False
        self.assertFalse(self.engine.has_speech())

        # After speech detected
        self.engine.vad.speech_detected = True
        self.assertTrue(self.engine.has_speech())

    def test_get_audio_duration_empty(self):
        """Test get_audio_duration with no audio frames."""
        self.engine.audio_frames = []
        self.assertEqual(self.engine.get_audio_duration(), 0.0)

    def test_get_audio_duration_with_frames(self):
        """Test get_audio_duration with audio frames."""
        # Create mock audio frames
        # Assuming 16000 Hz, 1 channel, 16-bit (2 bytes per sample)
        # 1 second of audio = 16000 samples = 32000 bytes
        self.engine.sample_rate = 16000
        self.engine.channels = 1
        self.engine.audio_frames = [b'\x00' * 16000, b'\x00' * 16000]  # 2 chunks of 8000 samples each

        # Total bytes = 32000, bytes_per_second = 16000 * 1 * 2 = 32000
        # Duration should be 32000 / 32000 = 1.0 second
        duration = self.engine.get_audio_duration()
        self.assertEqual(duration, 1.0)


if __name__ == '__main__':
    unittest.main()
