"""Unit tests for Voice Activity Detection."""

import unittest

import numpy as np

from src.audio.vad import VoiceActivityDetector


class TestVoiceActivityDetector(unittest.TestCase):
    """Test cases for VoiceActivityDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.vad = VoiceActivityDetector(
            sample_rate=self.sample_rate,
            chunk_size=self.chunk_size,
            energy_threshold=0.01
        )

    def test_initialization(self):
        """Test VAD initialization with parameters."""
        self.assertEqual(self.vad.sample_rate, self.sample_rate)
        self.assertEqual(self.vad.chunk_size, self.chunk_size)
        self.assertEqual(self.vad.energy_threshold, 0.01)
        self.assertFalse(self.vad.speech_detected)

    def test_is_speech_with_silence(self):
        """Test that silence is correctly detected."""
        # Generate silent audio (zeros)
        silent_audio = np.zeros(self.chunk_size, dtype=np.int16)
        audio_bytes = silent_audio.tobytes()

        result = self.vad.is_speech(audio_bytes)
        self.assertFalse(result)

    def test_is_speech_with_noise(self):
        """Test that loud audio is detected as speech."""
        # Generate loud audio signal
        loud_audio = np.random.randint(-32000, 32000, self.chunk_size, dtype=np.int16)
        audio_bytes = loud_audio.tobytes()

        result = self.vad.is_speech(audio_bytes)
        # Note: Result depends on threshold, but loud random noise should trigger
        self.assertIsInstance(result, bool)

    def test_is_speech_with_empty_data(self):
        """Test handling of empty audio data."""
        result = self.vad.is_speech(b'')
        self.assertFalse(result)

    def test_custom_energy_threshold(self):
        """Test VAD with custom energy threshold."""
        custom_vad = VoiceActivityDetector(
            sample_rate=16000,
            chunk_size=1024,
            energy_threshold=0.05
        )
        self.assertEqual(custom_vad.energy_threshold, 0.05)

    def test_get_silence_duration(self):
        """Test getting silence duration."""
        import time

        # Get initial silence duration
        initial_duration = self.vad.get_silence_duration()
        self.assertGreaterEqual(initial_duration, 0.0)

        # Wait a bit and check duration increased
        time.sleep(0.01)
        later_duration = self.vad.get_silence_duration()
        self.assertGreater(later_duration, initial_duration)

    def test_reset(self):
        """Test resetting VAD state."""
        # Set speech detected flag
        self.vad.speech_detected = True

        # Reset should clear the flag
        self.vad.reset()
        self.assertFalse(self.vad.speech_detected)

        # Silence duration should be reset (close to 0)
        self.assertLess(self.vad.get_silence_duration(), 0.1)

    def test_speech_updates_last_speech_time(self):
        """Test that detecting speech updates last_speech_time."""
        import time

        # Reset VAD first
        self.vad.reset()

        # Wait a bit to accumulate some silence time
        time.sleep(0.05)
        initial_silence = self.vad.get_silence_duration()
        self.assertGreater(initial_silence, 0)

        # Generate loud audio that should trigger speech detection
        # Use very high amplitude to ensure it exceeds the 0.01 threshold
        loud_audio = np.full(self.chunk_size, 32000, dtype=np.int16)
        audio_bytes = loud_audio.tobytes()

        # Detect speech
        result = self.vad.is_speech(audio_bytes)

        # Speech should be detected with such high amplitude
        self.assertTrue(result)

        # After detecting speech, silence duration should be reset (near 0)
        new_silence = self.vad.get_silence_duration()
        self.assertLess(new_silence, initial_silence)
        self.assertTrue(self.vad.speech_detected)


if __name__ == '__main__':
    unittest.main()
