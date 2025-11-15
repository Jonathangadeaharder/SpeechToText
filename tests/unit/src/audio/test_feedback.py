"""Unit tests for Audio Feedback generation."""

import unittest

import numpy as np

from src.audio.feedback import AudioFeedback


class TestAudioFeedback(unittest.TestCase):
    """Test cases for AudioFeedback class."""

    def test_generate_beep_returns_bytes(self):
        """Test that generate_beep returns audio data as bytes."""
        frequency = 440  # A4 note
        duration = 100  # 100ms

        beep = AudioFeedback.generate_beep(frequency, duration)

        self.assertIsInstance(beep, bytes)
        self.assertGreater(len(beep), 0)

    def test_generate_beep_with_custom_sample_rate(self):
        """Test beep generation with custom sample rate."""
        frequency = 880  # A5 note
        duration = 50
        sample_rate = 22050

        beep = AudioFeedback.generate_beep(frequency, duration, sample_rate)

        self.assertIsInstance(beep, bytes)
        # Verify approximate expected length (duration * sample_rate * 2 bytes per sample)
        expected_length = int((duration / 1000) * sample_rate * 2)
        self.assertAlmostEqual(len(beep), expected_length, delta=100)

    def test_generate_beep_different_frequencies(self):
        """Test generating beeps at different frequencies."""
        frequencies = [220, 440, 880, 1760]
        duration = 50

        for freq in frequencies:
            beep = AudioFeedback.generate_beep(freq, duration)
            self.assertIsInstance(beep, bytes)
            self.assertGreater(len(beep), 0)

    def test_generate_beep_different_durations(self):
        """Test generating beeps of different durations."""
        frequency = 440
        durations = [10, 50, 100, 200]

        previous_length = 0
        for duration in durations:
            beep = AudioFeedback.generate_beep(frequency, duration)
            current_length = len(beep)
            # Longer duration should produce more audio data
            self.assertGreater(current_length, previous_length)
            previous_length = current_length


if __name__ == '__main__':
    unittest.main()
