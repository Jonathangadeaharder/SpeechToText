"""Audio feedback generation for the dictation tool."""

import logging
from typing import Any

import numpy as np
import pyaudio


# Constants for audio feedback (avoiding magic numbers)
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_AUDIO_FORMAT = pyaudio.paInt16
DEFAULT_CHANNELS = 1
FADE_PERCENTAGE = 0.1  # Fade in/out duration as percentage of total duration
AUDIO_AMPLITUDE_MAX = 32767  # Maximum amplitude for 16-bit PCM


class AudioFeedback:
    """Generate and play audio feedback beeps."""

    @staticmethod
    def generate_beep(frequency: int, duration: int, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
        """
        Generate a beep sound.

        Args:
            frequency: Frequency of the beep in Hz
            duration: Duration of the beep in milliseconds
            sample_rate: Sample rate in Hz

        Returns:
            Raw PCM audio data as bytes
        """
        samples = int(sample_rate * duration / 1000)
        t = np.linspace(0, duration / 1000, samples, False)
        wave_data = np.sin(frequency * t * 2 * np.pi)

        # Apply fade in/out to avoid clicks
        fade_samples = int(samples * FADE_PERCENTAGE)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        wave_data[:fade_samples] *= fade_in
        wave_data[-fade_samples:] *= fade_out

        # Convert to 16-bit PCM
        audio = (wave_data * AUDIO_AMPLITUDE_MAX).astype(np.int16)
        return audio.tobytes()

    @staticmethod
    def play_beep(frequency: int, duration: int, pyaudio_instance: Any) -> None:
        """
        Play a beep sound.

        Args:
            frequency: Frequency of the beep in Hz
            duration: Duration of the beep in milliseconds
            pyaudio_instance: PyAudio instance to use for playback
        """
        stream = None
        try:
            beep_data = AudioFeedback.generate_beep(frequency, duration)
            stream = pyaudio_instance.open(
                format=DEFAULT_AUDIO_FORMAT,
                channels=DEFAULT_CHANNELS,
                rate=DEFAULT_SAMPLE_RATE,
                output=True
            )
            stream.write(beep_data)
        except Exception as e:
            logging.warning(f"Failed to play beep: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
