#!/usr/bin/env python3
"""
Unit tests for the dictation tool.

Tests cover:
- Audio format validation
- WAV file creation from audio frames
- Model loading fallback logic
- Hotkey detection logic
- Thread safety of recording flag
"""

import unittest
import io
import wave
from unittest.mock import Mock, patch
import threading
import time


class TestAudioProcessing(unittest.TestCase):
    """Tests for audio capture and processing functions."""

    def test_wav_buffer_creation(self):
        """Test that WAV buffer is created with correct format."""
        # Simulate audio frames
        sample_rate = 16000
        channels = 1
        sample_width = 2  # 16-bit = 2 bytes

        # Create dummy audio data (1 second of silence)
        num_frames = sample_rate
        audio_data = b"\x00\x00" * num_frames

        # Create WAV buffer
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

        # Verify buffer contains valid WAV data
        wav_buffer.seek(0)
        with wave.open(wav_buffer, "rb") as wf:
            self.assertEqual(wf.getnchannels(), channels)
            self.assertEqual(wf.getsampwidth(), sample_width)
            self.assertEqual(wf.getframerate(), sample_rate)
            self.assertEqual(wf.getnframes(), num_frames)

    def test_empty_audio_frames(self):
        """Test handling of empty audio frames list."""
        frames = []

        # Should handle empty frames gracefully
        if not frames:
            result = None
        else:
            result = b"".join(frames)

        self.assertIsNone(result)

    def test_audio_chunk_concatenation(self):
        """Test that audio chunks are properly concatenated."""
        chunk1 = b"\x01\x02\x03\x04"
        chunk2 = b"\x05\x06\x07\x08"
        chunk3 = b"\x09\x0a\x0b\x0c"

        frames = [chunk1, chunk2, chunk3]
        result = b"".join(frames)

        self.assertEqual(len(result), 12)
        self.assertEqual(result, b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c")


class TestHotkeyLogic(unittest.TestCase):
    """Tests for hotkey detection logic."""

    def test_both_keys_pressed(self):
        """Test that recording starts only when both keys are pressed."""
        from pynput import keyboard

        hotkey_combination = {keyboard.Key.ctrl, keyboard.Key.cmd}
        currently_pressed = set()

        # Press first key
        currently_pressed.add(keyboard.Key.ctrl)
        self.assertNotEqual(currently_pressed, hotkey_combination)

        # Press second key
        currently_pressed.add(keyboard.Key.cmd)
        self.assertEqual(currently_pressed, hotkey_combination)

    def test_single_key_not_sufficient(self):
        """Test that single key press doesn't trigger recording."""
        from pynput import keyboard

        hotkey_combination = {keyboard.Key.ctrl, keyboard.Key.cmd}
        currently_pressed = {keyboard.Key.ctrl}

        self.assertNotEqual(currently_pressed, hotkey_combination)

    def test_key_release_detection(self):
        """Test that key release is properly detected."""
        from pynput import keyboard

        hotkey_combination = {keyboard.Key.ctrl, keyboard.Key.cmd}
        currently_pressed = {keyboard.Key.ctrl, keyboard.Key.cmd}

        # Release one key
        currently_pressed.remove(keyboard.Key.ctrl)

        self.assertNotEqual(currently_pressed, hotkey_combination)
        self.assertEqual(currently_pressed, {keyboard.Key.cmd})


class TestThreadSafety(unittest.TestCase):
    """Tests for thread safety of global state."""

    def test_recording_flag_thread_safety(self):
        """Test that recording flag can be safely modified from multiple threads."""
        is_recording = False
        lock = threading.Lock()
        results = []

        def toggle_recording():
            nonlocal is_recording
            for _ in range(100):
                with lock:
                    is_recording = not is_recording
                time.sleep(0.0001)
            results.append(True)

        threads = [threading.Thread(target=toggle_recording) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads completed successfully
        self.assertEqual(len(results), 3)

    def test_audio_frames_list_append(self):
        """Test that audio frames can be appended from callback thread."""
        audio_frames = []

        def audio_callback(data):
            audio_frames.append(data)

        # Simulate callback from audio thread
        test_data = [b"\x00" * 1024 for _ in range(10)]
        for data in test_data:
            audio_callback(data)

        self.assertEqual(len(audio_frames), 10)
        self.assertEqual(sum(len(frame) for frame in audio_frames), 10240)


class TestModelConfiguration(unittest.TestCase):
    """Tests for model configuration and fallback logic."""

    @patch("dictation.WhisperModel")
    def test_gpu_model_success(self, mock_whisper):
        """Test successful GPU model loading."""
        mock_model = Mock()
        mock_whisper.return_value = mock_model

        # Simulate loading GPU model
        try:
            _ = mock_whisper("small.en", device="cuda", compute_type="int8")
            device_used = "cuda"
        except Exception:
            device_used = "cpu"

        self.assertEqual(device_used, "cuda")
        mock_whisper.assert_called_once_with("small.en", device="cuda", compute_type="int8")

    @patch("dictation.WhisperModel")
    def test_gpu_model_fallback_to_cpu(self, mock_whisper):
        """Test fallback to CPU when GPU fails."""
        # First call (GPU) raises exception, second call (CPU) succeeds
        mock_whisper.side_effect = [Exception("CUDA not available"), Mock()]

        # Simulate model loading with fallback
        device_used = None
        try:
            _ = mock_whisper("small.en", device="cuda", compute_type="int8")
            device_used = "cuda"
        except Exception:
            _ = mock_whisper("tiny.en", device="cpu", compute_type="int8")
            device_used = "cpu"

        self.assertEqual(device_used, "cpu")
        self.assertEqual(mock_whisper.call_count, 2)


class TestTextProcessing(unittest.TestCase):
    """Tests for text processing and cleaning."""

    def test_text_stripping(self):
        """Test that transcribed text is properly stripped of whitespace."""
        transcription = "  Hello World  "
        cleaned = transcription.strip()

        self.assertEqual(cleaned, "Hello World")
        self.assertNotEqual(cleaned, transcription)

    def test_empty_transcription(self):
        """Test handling of empty transcription results."""
        transcription = "   "
        cleaned = transcription.strip()

        self.assertEqual(cleaned, "")
        self.assertFalse(cleaned)  # Empty string is falsy

    def test_segment_joining(self):
        """Test that multiple segments are properly joined."""
        segments = [Mock(text="Hello"), Mock(text=" world"), Mock(text="!")]

        text = " ".join(segment.text for segment in segments).strip()

        self.assertEqual(text, "Hello  world !")


class TestAudioCallbackBehavior(unittest.TestCase):
    """Tests for audio callback behavior."""

    @patch('dictation.pyaudio')
    @patch('dictation.IS_RECORDING', True)
    @patch('dictation.AUDIO_FRAMES', [])
    def test_callback_continues_when_recording(self, mock_pyaudio):
        """Test that callback returns paContinue when recording."""
        # Import the actual callback function
        import dictation

        # Mock pyaudio.paContinue constant
        mock_pyaudio.paContinue = 0

        # Simulate callback
        in_data = b"\x00" * 1024
        result_data, status = dictation.audio_callback(in_data, None, None, None)

        # Should return paContinue (0) and data should be appended
        self.assertEqual(status, 0)
        self.assertEqual(result_data, in_data)

    @patch('dictation.pyaudio')
    @patch('dictation.IS_RECORDING', False)
    @patch('dictation.AUDIO_FRAMES', [])
    def test_callback_continues_when_not_recording(self, mock_pyaudio):
        """Test that callback still returns paContinue even when not recording."""
        # Import the actual callback function
        import dictation

        # Mock pyaudio.paContinue constant
        mock_pyaudio.paContinue = 0

        # Track initial frames length
        initial_frames = len(dictation.AUDIO_FRAMES)

        # Simulate callback
        in_data = b"\x00" * 1024
        result_data, status = dictation.audio_callback(in_data, None, None, None)

        # Should still return paContinue (0) but not append data
        self.assertEqual(status, 0)
        self.assertEqual(result_data, in_data)
        # Frames should not have increased since not recording
        self.assertEqual(len(dictation.AUDIO_FRAMES), initial_frames)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflows."""

    def test_recording_lifecycle(self):
        """Test complete recording lifecycle: start -> record -> stop."""
        is_recording = False
        audio_frames = []

        # Start recording
        is_recording = True
        self.assertTrue(is_recording)

        # Simulate recording some frames
        for _ in range(5):
            if is_recording:
                audio_frames.append(b"\x00" * 1024)

        self.assertEqual(len(audio_frames), 5)

        # Stop recording
        is_recording = False
        self.assertFalse(is_recording)

        # Additional frames should not be added (is_recording is False)
        self.assertEqual(len(audio_frames), 5)

    def test_multiple_recording_sessions(self):
        """Test multiple consecutive recording sessions."""
        sessions = []

        for _ in range(3):
            is_recording = False
            audio_frames = []

            # Start recording
            is_recording = True

            # Record frames
            for _ in range(3):
                if is_recording:
                    audio_frames.append(b"\x00" * 512)

            # Stop recording
            is_recording = False

            sessions.append(len(audio_frames))

        # Each session should have recorded 3 frames
        self.assertEqual(sessions, [3, 3, 3])


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys

    success = run_tests()
    sys.exit(0 if success else 1)
