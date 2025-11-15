"""Voice Activity Detection for the dictation tool."""

import time

import numpy as np


# Constants for Voice Activity Detection (avoiding magic numbers)
DEFAULT_ENERGY_THRESHOLD = 0.01
AUDIO_MAX_AMPLITUDE = 32767  # Maximum amplitude for 16-bit PCM audio


class VoiceActivityDetector:
    """Detect silence/speech using audio energy analysis."""

    def __init__(
        self,
        sample_rate: int,
        chunk_size: int,
        energy_threshold: float = DEFAULT_ENERGY_THRESHOLD
    ):
        """
        Initialize Voice Activity Detector.

        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Audio chunk size in samples
            energy_threshold: Energy threshold for speech detection (0.0-1.0)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.energy_threshold = energy_threshold
        self.last_speech_time = time.time()
        self.speech_detected = False

    def is_speech(self, audio_data: bytes) -> bool:
        """
        Detect if audio chunk contains speech using RMS energy.

        Args:
            audio_data: Raw audio bytes (16-bit PCM)

        Returns:
            True if speech detected, False if silence
        """
        # Convert bytes to numpy array
        if not audio_data or len(audio_data) == 0:
            return False

        # Validate buffer length is a multiple of 2 (for 16-bit audio)
        if len(audio_data) % 2 != 0:
            # Truncate odd byte to avoid frombuffer error
            audio_data = audio_data[:-1]
            if len(audio_data) == 0:
                return False

        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        if len(audio_array) == 0:
            return False

        # Calculate RMS (Root Mean Square) energy
        # Use float64 to avoid overflow, then clip to prevent sqrt of negative
        mean_square = np.mean(audio_array.astype(np.float64) ** 2)
        rms = np.sqrt(np.maximum(mean_square, 0))

        # Normalize to 0-1 range (16-bit audio has max value of AUDIO_MAX_AMPLITUDE)
        normalized_rms = rms / AUDIO_MAX_AMPLITUDE

        # Detect speech if energy exceeds threshold
        is_speech_detected = bool(normalized_rms > self.energy_threshold)

        if is_speech_detected:
            self.last_speech_time = time.time()
            self.speech_detected = True

        return is_speech_detected

    def get_silence_duration(self) -> float:
        """
        Get duration of silence in seconds since last speech.

        Returns:
            Silence duration in seconds
        """
        return time.time() - self.last_speech_time

    def reset(self) -> None:
        """Reset the detector state."""
        self.last_speech_time = time.time()
        self.speech_detected = False
