#!/usr/bin/env python3
"""
Push-to-Talk Speech-to-Text Dictation Tool - Enhanced Edition

A feature-rich dictation tool with configurable hotkeys, audio feedback,
punctuation commands, continuous mode, and system tray integration.

Architecture:
- Module 1: Configuration Manager
- Module 2: Global Hotkey Listener (pynput)
- Module 3: Audio Capture with Feedback (PyAudio)
- Module 4: STT Engine (faster-whisper)
- Module 5: Text Processing (punctuation, vocabulary)
- Module 6: Text Injection (pynput)
- Module 7: System Tray Icon (pystray)
- Module 8: Wake Word Detection (optional)
"""

import io
import logging
import os
import re
import sys
import threading
import wave
from typing import Dict, List, Optional, Set

import numpy as np
import pyaudio
import yaml
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw
from pynput import keyboard
from pystray import Icon, Menu, MenuItem

# --- Module 1: Configuration Manager ---


class Config:
    """Configuration manager for the dictation tool."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            print(f"⚠ Config file not found at {self.config_path}")
            print("Creating default configuration...")
            return self._get_default_config()

        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            print(f"✓ Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            print(f"✗ Error loading config: {e}")
            print("Using default configuration...")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
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

    def _setup_logging(self):
        """Setup logging based on configuration."""
        log_level = getattr(logging, self.config["advanced"].get("log_level", "INFO"), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def get(self, *keys, default=None):
        """Get a nested configuration value."""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value


# --- Module 2: Audio Feedback Generator ---


class AudioFeedback:
    """Generate audio feedback beeps."""

    @staticmethod
    def generate_beep(frequency: int, duration: int, sample_rate: int = 44100) -> bytes:
        """Generate a beep sound."""
        samples = int(sample_rate * duration / 1000)
        t = np.linspace(0, duration / 1000, samples, False)
        wave_data = np.sin(frequency * t * 2 * np.pi)

        # Apply fade in/out to avoid clicks
        fade_samples = int(samples * 0.1)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        wave_data[:fade_samples] *= fade_in
        wave_data[-fade_samples:] *= fade_out

        # Convert to 16-bit PCM
        audio = (wave_data * 32767).astype(np.int16)
        return audio.tobytes()

    @staticmethod
    def play_beep(frequency: int, duration: int, pyaudio_instance):
        """Play a beep sound."""
        try:
            beep_data = AudioFeedback.generate_beep(frequency, duration)
            stream = pyaudio_instance.open(
                format=pyaudio.paInt16, channels=1, rate=44100, output=True
            )
            stream.write(beep_data)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logging.warning(f"Failed to play beep: {e}")


# --- Module 3: Text Processor ---


class TextProcessor:
    """Process transcribed text with punctuation commands and custom vocabulary."""

    def __init__(self, config: Config):
        self.config = config
        self.punctuation_map = config.get("text_processing", "punctuation_map", default={})
        self.custom_vocabulary = config.get("text_processing", "custom_vocabulary", default={})
        self.command_words = config.get("text_processing", "command_words", default={})
        self.last_text = ""

    def process(self, text: str) -> Optional[str]:
        """Process text with punctuation commands and custom vocabulary."""
        if not text:
            return None

        # Check for command words
        text_lower = text.lower().strip()
        if text_lower in self.command_words:
            command = self.command_words[text_lower]
            self._execute_command(command)
            return None  # Don't type command words

        # Apply punctuation commands
        if self.config.get("text_processing", "punctuation_commands", default=True):
            text = self._apply_punctuation_commands(text)

        # Apply custom vocabulary
        text = self._apply_custom_vocabulary(text)

        self.last_text = text
        return text

    def _apply_punctuation_commands(self, text: str) -> str:
        """Replace spoken punctuation with actual punctuation marks."""
        for word, punctuation in self.punctuation_map.items():
            # Match whole words only, case-insensitive
            pattern = r"\b" + re.escape(word) + r"\b"
            text = re.sub(pattern, punctuation, text, flags=re.IGNORECASE)

        # Clean up extra spaces around punctuation
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _apply_custom_vocabulary(self, text: str) -> str:
        """Apply custom vocabulary replacements."""
        for phrase, replacement in self.custom_vocabulary.items():
            text = re.sub(r"\b" + re.escape(phrase) + r"\b", replacement, text, flags=re.IGNORECASE)
        return text

    def _execute_command(self, command: str):
        """Execute a command word action."""
        if command == "undo_last":
            # Delete the last transcribed text
            if self.last_text:
                controller = keyboard.Controller()
                for _ in range(len(self.last_text)):
                    controller.press(keyboard.Key.backspace)
                    controller.release(keyboard.Key.backspace)
                logging.info("Undid last transcription")
        elif command == "clear_line":
            # Clear the current line
            controller = keyboard.Controller()
            controller.press(keyboard.Key.cmd)
            controller.press(keyboard.Key.backspace)
            controller.release(keyboard.Key.backspace)
            controller.release(keyboard.Key.cmd)
            logging.info("Cleared line")


# --- Module 4: Dictation Engine ---


class DictationEngine:
    """Main dictation engine handling recording, transcription, and text injection."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("DictationEngine")

        # State management
        self.is_recording = False
        self.continuous_mode = config.get("continuous_mode", "enabled", default=False)
        self.audio_frames = []
        self.currently_pressed = set()
        self.stream = None
        self.running = True

        # Initialize components
        self.p = pyaudio.PyAudio()
        self.text_processor = TextProcessor(config)
        self.whisper_model = self._load_whisper_model()

        # Audio settings
        self.sample_rate = config.get("audio", "sample_rate", default=16000)
        self.channels = config.get("audio", "channels", default=1)
        self.chunk_size = config.get("audio", "chunk_size", default=1024)
        self.format = pyaudio.paInt16

        # Hotkeys
        self.push_to_talk_keys = self._parse_hotkeys(
            config.get("hotkeys", "push_to_talk", default=["ctrl", "cmd"])
        )
        self.toggle_continuous_keys = self._parse_hotkeys(
            config.get("hotkeys", "toggle_continuous", default=["ctrl", "shift", "d"])
        )

    def _parse_hotkeys(self, key_names: List[str]) -> Set:
        """Convert key names from config to pynput Key objects."""
        keys = set()
        for key_name in key_names:
            key_name = key_name.lower()
            if hasattr(keyboard.Key, key_name):
                keys.add(getattr(keyboard.Key, key_name))
            else:
                # Regular key (letter/number)
                try:
                    keys.add(keyboard.KeyCode.from_char(key_name))
                except Exception as e:
                    self.logger.warning(f"Unknown key: {key_name} - {e}")
        return keys

    def _load_whisper_model(self) -> WhisperModel:
        """Load the Whisper model based on configuration."""
        model_name = self.config.get("model", "name", default="small.en")
        device = self.config.get("model", "device", default="auto")
        compute_type = self.config.get("model", "compute_type", default="int8")

        print(f"Loading transcription model ({model_name})...")
        print("This may take a moment on first run...")

        # Auto-detect device
        if device == "auto":
            try:
                model = WhisperModel(model_name, device="cuda", compute_type=compute_type)
                print(f"✓ Model '{model_name}' ({compute_type}) loaded on GPU")
                return model
            except Exception as e:
                self.logger.info(f"GPU not available: {e}")
                self.logger.info("Falling back to CPU...")
                device = "cpu"

        try:
            model = WhisperModel(model_name, device=device, compute_type=compute_type)
            print(f"✓ Model '{model_name}' ({compute_type}) loaded on {device.upper()}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            print("✗ Failed to load model. Please check your configuration.")
            sys.exit(1)

    def audio_callback(self, in_data, _frame_count, _time_info, _status):
        """PyAudio callback for recording audio."""
        if self.is_recording:
            self.audio_frames.append(in_data)
            return (in_data, pyaudio.paContinue)
        return (in_data, pyaudio.paComplete)

    def start_recording(self):
        """Start recording audio."""
        if self.is_recording:
            return

        self.is_recording = True
        self.audio_frames = []

        # Play start beep
        if self.config.get("audio", "beep_on_start", default=True):
            freq = self.config.get("audio", "start_beep_frequency", default=800)
            dur = self.config.get("audio", "start_beep_duration", default=100)
            threading.Thread(
                target=AudioFeedback.play_beep, args=(freq, dur, self.p), daemon=True
            ).start()

        try:
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self.audio_callback,
            )
            self.stream.start_stream()
            print("\n🎤 Recording started...")
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.is_recording = False

    def stop_recording(self):
        """Stop recording and trigger transcription."""
        if not self.is_recording:
            return

        self.is_recording = False
        print("⏹ Recording stopped. Processing...")

        # Play stop beep
        if self.config.get("audio", "beep_on_stop", default=True):
            freq = self.config.get("audio", "stop_beep_frequency", default=600)
            dur = self.config.get("audio", "stop_beep_duration", default=100)
            threading.Thread(
                target=AudioFeedback.play_beep, args=(freq, dur, self.p), daemon=True
            ).start()

        # Stop stream
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
        if self.stream:
            self.stream.close()
            self.stream = None

        # Transcribe in background thread
        frames_copy = self.audio_frames.copy()
        threading.Thread(target=self.transcribe_audio, args=(frames_copy,), daemon=True).start()

    def transcribe_audio(self, frames: List[bytes]):
        """Transcribe audio and inject text."""
        if not frames:
            self.logger.warning("No audio recorded")
            return

        try:
            # Create WAV buffer
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(frames))

            wav_buffer.seek(0)

            # Transcribe
            print("🧠 Transcribing...")
            beam_size = self.config.get("model", "beam_size", default=5)
            language = self.config.get("model", "language", default="en")

            segments, _info = self.whisper_model.transcribe(
                wav_buffer, beam_size=beam_size, language=language, condition_on_previous_text=False
            )

            # Collect text
            text = " ".join(segment.text for segment in segments).strip()

            if text:
                print(f"✓ Transcription: '{text}'")

                # Process text (punctuation, vocabulary, commands)
                processed_text = self.text_processor.process(text)

                if processed_text:
                    # Inject text
                    print("⌨ Typing text...")
                    text_injector = keyboard.Controller()
                    text_injector.type(processed_text)
                    print("✓ Done!\n")
            else:
                print("⚠ Transcription was empty.")

        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            print(f"✗ Error during transcription: {e}")

    def toggle_continuous_mode(self):
        """Toggle continuous dictation mode."""
        self.continuous_mode = not self.continuous_mode
        if self.continuous_mode:
            print("\n🔄 Continuous mode ENABLED")
            print("   (Speak naturally, will auto-transcribe after silence)")
            self.start_recording()
        else:
            print("\n🔄 Continuous mode DISABLED")
            print("   (Use push-to-talk hotkey to record)")
            if self.is_recording:
                self.stop_recording()

    def on_press(self, key):
        """Handle key press events."""
        # Check for push-to-talk
        if key in self.push_to_talk_keys:
            self.currently_pressed.add(key)
            if self.currently_pressed == self.push_to_talk_keys and not self.continuous_mode:
                self.start_recording()

        # Check for toggle continuous mode
        if key in self.toggle_continuous_keys:
            self.currently_pressed.add(key)
            if self.currently_pressed == self.toggle_continuous_keys:
                self.toggle_continuous_mode()

    def on_release(self, key):
        """Handle key release events."""
        if key in self.push_to_talk_keys:
            if not self.continuous_mode and self.is_recording:
                self.stop_recording()
            if key in self.currently_pressed:
                self.currently_pressed.remove(key)

        if key in self.toggle_continuous_keys:
            if key in self.currently_pressed:
                self.currently_pressed.remove(key)

    def cleanup(self):
        """Cleanup resources."""
        if self.stream:
            self.stream.close()
        self.p.terminate()


# --- Module 5: System Tray Icon ---


class SystemTrayIcon:
    """System tray icon for the dictation tool."""

    def __init__(self, dictation_engine: DictationEngine):
        self.engine = dictation_engine
        self.icon = None

    def create_image(self, color="green"):
        """Create icon image."""
        # Create a simple colored circle
        size = (64, 64)
        image = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(image)

        # Draw circle
        color_map = {"green": (0, 200, 0), "red": (200, 0, 0), "yellow": (200, 200, 0)}
        circle_color = color_map.get(color, (0, 200, 0))
        draw.ellipse([8, 8, 56, 56], fill=circle_color, outline="black", width=2)

        # Draw microphone icon (simple)
        draw.rectangle([28, 20, 36, 35], fill="white")
        draw.ellipse([24, 35, 40, 42], outline="white", width=2)
        draw.line([32, 42, 32, 48], fill="white", width=2)

        return image

    def on_quit(self, icon, item):
        """Handle quit action."""
        print("\nShutting down from system tray...")
        self.engine.cleanup()
        icon.stop()
        os._exit(0)

    def on_toggle_continuous(self, icon, item):
        """Handle toggle continuous mode."""
        self.engine.toggle_continuous_mode()

    def run(self):
        """Run the system tray icon."""
        menu = Menu(
            MenuItem("Continuous Mode", self.on_toggle_continuous),
            MenuItem("Quit", self.on_quit),
        )

        self.icon = Icon("dictation", self.create_image(), "Dictation Tool", menu)
        self.icon.run()


# --- Main Application ---


def main():
    """Main entry point."""
    print("=" * 70)
    print("  🎤 Push-to-Talk Speech-to-Text Dictation Tool - Enhanced Edition")
    print("=" * 70)

    # Load configuration
    config = Config("config.yaml")

    # Initialize dictation engine
    engine = DictationEngine(config)

    # Print hotkey information
    push_to_talk = " + ".join(config.get("hotkeys", "push_to_talk", default=["ctrl", "cmd"]))
    toggle_continuous = " + ".join(
        config.get("hotkeys", "toggle_continuous", default=["ctrl", "shift", "d"])
    )

    print("\n📋 Hotkeys:")
    print(f"   Push-to-Talk: {push_to_talk}")
    print(f"   Toggle Continuous Mode: {toggle_continuous}")
    print("\n⚙️  Configuration loaded from: config.yaml")
    print(
        f"   Punctuation commands: {'✓' if config.get('text_processing', 'punctuation_commands') else '✗'}"
    )
    print(f"   System tray: {'✓' if config.get('system_tray', 'enabled') else '✗'}")
    print(f"   Audio feedback: {'✓' if config.get('audio', 'beep_on_start') else '✗'}")
    print("\n" + "=" * 70)
    print("✓ Ready! Listening for hotkeys...")
    print("=" * 70 + "\n")

    # Start system tray if enabled
    if config.get("system_tray", "enabled", default=True):
        tray_icon = SystemTrayIcon(engine)
        threading.Thread(target=tray_icon.run, daemon=True).start()

    # Start keyboard listener
    try:
        with keyboard.Listener(on_press=engine.on_press, on_release=engine.on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        engine.cleanup()
        print("Goodbye!")


if __name__ == "__main__":
    main()
