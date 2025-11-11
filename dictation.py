#!/usr/bin/env python3
"""
Push-to-Talk Speech-to-Text Dictation Tool

A lightweight, CPU/GPU-friendly dictation tool that uses the faster-whisper library.
Hold Ctrl+Win (or Ctrl+Cmd on Mac) to record, release to transcribe and type.

Architecture:
- Module 1: Global Hotkey Listener (pynput)
- Module 2: Audio Capture (PyAudio)
- Module 3: STT Engine (faster-whisper)
- Module 4: Text Injection (pynput)
"""

import io
import sys
import threading
import wave

import pyaudio
from faster_whisper import WhisperModel
from pynput import keyboard

# --- Configuration ---
HOTKEY_COMBINATION = {keyboard.Key.ctrl, keyboard.Key.cmd}  # .cmd is Win key on Windows/Linux, Cmd key on macOS
CURRENTLY_PRESSED = set()
IS_RECORDING = False
AUDIO_FRAMES = []
# Thread synchronization
RECORDING_LOCK = threading.Lock()
FRAMES_LOCK = threading.Lock()
PRESSED_LOCK = threading.Lock()
STREAM_LOCK = threading.Lock()

# Audio settings (optimized for Whisper)
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024

# --- Module 3: STT Engine (Load model once at start) ---
print("Loading transcription model (faster-whisper)...")
print("This may take a moment on first run...")

# Try to load GPU-accelerated model first, fall back to CPU if needed
WHISPER_MODEL = None
try:
    # Load 'small' model with int8 quantization to fit in 2GB VRAM
    # This provides excellent quality while staying within VRAM constraints
    WHISPER_MODEL = WhisperModel(
        "small.en", device="cuda", compute_type="int8"  # English-only model for better performance
    )
    print("✓ Model 'small.en' (int8) loaded on GPU. Ready.")
    print("  VRAM usage: ~1.5GB (safe for 2GB VRAM)")
except Exception as e:
    print(f"⚠ GPU model failed to load: {e}")
    print("Falling back to CPU model. This will be slower but still functional.")
    try:
        # Fallback to tiny CPU model if GPU/CUDA fails
        WHISPER_MODEL = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        print("✓ Model 'tiny.en' loaded on CPU. Ready.")
    except Exception as e:
        print(f"✗ Failed to load any model: {e}")
        print("Please ensure faster-whisper is properly installed.")
        print("Run: pip install faster-whisper")
        sys.exit(1)

# --- Module 2: Audio Capture ---
p = pyaudio.PyAudio()
STREAM = None


def audio_callback(in_data, _frame_count, _time_info, _status):
    """
    Callback function called by PyAudio in a separate thread.
    Appends audio data to buffer while recording flag is True.
    """
    with RECORDING_LOCK:
        is_recording = IS_RECORDING

    if is_recording:
        with FRAMES_LOCK:
            AUDIO_FRAMES.append(in_data)

    return (in_data, pyaudio.paContinue)


def start_recording():
    """
    Called by the hotkey press event.
    Initializes audio stream and begins capturing microphone input.
    """
    global IS_RECORDING, AUDIO_FRAMES, STREAM

    with RECORDING_LOCK:
        if IS_RECORDING:
            return  # Already recording
        IS_RECORDING = True

    with FRAMES_LOCK:
        AUDIO_FRAMES = []

    try:
        with STREAM_LOCK:
            STREAM = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=audio_callback,
            )
            STREAM.start_stream()
        print("\n🎤 Recording started...")
    except Exception as e:
        print(f"✗ Failed to start recording: {e}")
        with RECORDING_LOCK:
            IS_RECORDING = False


def stop_and_process_recording():
    """
    Called by the hotkey release event.
    Stops audio capture and triggers transcription in a worker thread.
    """
    global IS_RECORDING

    with RECORDING_LOCK:
        if not IS_RECORDING:
            return
        IS_RECORDING = False

    print("⏹ Recording stopped. Processing...")

    # Wait for the stream to finish writing its last buffer
    with STREAM_LOCK:
        if STREAM and STREAM.is_active():
            STREAM.stop_stream()
        if STREAM:
            STREAM.close()

    # Copy frames to a new thread to avoid blocking the listener
    with FRAMES_LOCK:
        frames_copy = AUDIO_FRAMES.copy()
    threading.Thread(target=transcribe_audio, args=(frames_copy,), daemon=True).start()


def transcribe_audio(frames):
    """
    Runs in a worker thread to process audio and inject text.

    Args:
        frames: List of audio data chunks captured from microphone
    """
    if not frames:
        print("⚠ No audio recorded.")
        return

    try:
        # Calculate sample size before creating WAV buffer
        # This avoids accessing PyAudio instance that may be terminated during shutdown
        sample_size = p.get_sample_size(FORMAT)

        # Save raw audio data to an in-memory WAV file
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(sample_size)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))

        wav_buffer.seek(0)

        # --- Module 3: Transcribe using faster-whisper ---
        print("🧠 Transcribing...")
        segments, _info = WHISPER_MODEL.transcribe(
            wav_buffer, beam_size=5, language="en", condition_on_previous_text=False
        )

        # Collect all transcribed text from segments
        text_to_paste = " ".join(segment.text for segment in segments).strip()

        if text_to_paste:
            print(f"✓ Transcription: '{text_to_paste}'")

            # --- Module 4: Inject Text ---
            print("⌨ Typing text...")
            text_injector = keyboard.Controller()
            text_injector.type(text_to_paste)
            print("✓ Done!\n")
        else:
            print("⚠ Transcription was empty.")

    except Exception as e:
        print(f"✗ Error during transcription: {e}")


# --- Module 1: Hotkey Listener ---
def on_press(key):
    """
    Callback for pynput listener when a key is pressed.
    Starts recording when both hotkeys are pressed.
    """
    if key in HOTKEY_COMBINATION:
        with PRESSED_LOCK:
            CURRENTLY_PRESSED.add(key)
            if CURRENTLY_PRESSED == HOTKEY_COMBINATION:
                start_recording()


def on_release(key):
    """
    Callback for pynput listener when a key is released.
    Stops recording and triggers transcription when either hotkey is released.
    """
    if key in HOTKEY_COMBINATION:
        with RECORDING_LOCK:
            is_recording = IS_RECORDING

        if is_recording:
            stop_and_process_recording()

        with PRESSED_LOCK:
            if key in CURRENTLY_PRESSED:
                CURRENTLY_PRESSED.remove(key)


# --- Main Application Logic ---
def main():
    """
    Main entry point. Sets up the keyboard listener and keeps the application running.
    """
    print("=" * 60)
    print("  Push-to-Talk Speech-to-Text Dictation Tool")
    print("=" * 60)
    print("\nHotkey: Ctrl+Win (or Ctrl+Cmd on Mac)")
    print("\nInstructions:")
    print("  1. Hold Ctrl+Win to start recording")
    print("  2. Speak your text")
    print("  3. Release keys to transcribe and type")
    print("\nPress Ctrl+C to exit.")
    print("=" * 60)
    print("\n✓ Ready! Listening for hotkey...\n")

    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        with STREAM_LOCK:
            if STREAM:
                STREAM.close()
        p.terminate()
        print("Goodbye!")


if __name__ == "__main__":
    main()
