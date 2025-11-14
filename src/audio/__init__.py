"""Audio processing components for the dictation tool."""

from src.audio.feedback import AudioFeedback
from src.audio.vad import VoiceActivityDetector

__all__ = ["AudioFeedback", "VoiceActivityDetector"]
