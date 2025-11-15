"""
Dictation Engine - Orchestrates the entire speech-to-text dictation system.

This is the core engine that coordinates:
- Audio capture and recording
- Speech transcription via Whisper
- Text processing and command parsing
- Command execution via registry
- Event publishing and lifecycle management
"""

import logging
import queue
import threading
import time
from typing import Optional

import numpy as np
import pyaudio
from faster_whisper import WhisperModel
from pynput import keyboard, mouse

from src.audio.feedback import AudioFeedback
from src.audio.vad import VoiceActivityDetector
from src.commands.base import CommandContext
from src.commands.parser import CommandParser
from src.commands.registry import CommandRegistry
from src.core.config import Config
from src.core.events import Event, EventBus, EventType
from src.overlays.element_overlay import ElementOverlay
from src.overlays.feedback_overlay import FeedbackOverlay
from src.overlays.grid_overlay import GridOverlay
from src.overlays.help_overlay import HelpOverlay
from src.overlays.manager import OverlayManager
from src.overlays.window_overlay import WindowListOverlay
from src.overlays.base import OverlayType
from src.transcription.text_processor import TextProcessor


class DictationEngine:
    """
    Core dictation engine that orchestrates all components.

    Responsibilities:
    - Manage audio recording lifecycle
    - Transcribe audio using Whisper
    - Process text through TextProcessor
    - Execute commands via CommandRegistry
    - Publish events through EventBus
    - Handle errors and cleanup
    """

    def __init__(
        self,
        config: Config,
        event_bus: EventBus,
        command_registry: CommandRegistry,
        text_processor: TextProcessor,
        parser: CommandParser,
    ):
        """
        Initialize the dictation engine.

        Args:
            config: Configuration object
            event_bus: Event bus for publishing events
            command_registry: Registry of available commands
            text_processor: Text processor for punctuation/vocabulary
            parser: Command parser for number extraction
        """
        self.config = config
        self.event_bus = event_bus
        self.command_registry = command_registry
        self.text_processor = text_processor
        self.parser = parser
        self.logger = logging.getLogger("DictationEngine")

        # Audio components
        self.audio_feedback = AudioFeedback()
        self.sample_rate = config.get("audio", "sample_rate", default=16000)
        self.channels = config.get("audio", "channels", default=1)
        self.chunk_size = config.get("audio", "chunk_size", default=1024)

        # Voice Activity Detection
        self.vad = VoiceActivityDetector(
            sample_rate=self.sample_rate,
            chunk_size=self.chunk_size,
            energy_threshold=0.01,
        )

        # PyAudio setup
        self.pyaudio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

        # Recording state
        self.is_recording = False
        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.audio_frames: list[bytes] = []

        # Whisper model
        self.model: Optional[WhisperModel] = None
        self.model_loading = False
        self._load_whisper_model()

        # Controllers for command execution
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()

        # Get screen dimensions
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
        except Exception as e:
            self.logger.warning(f"Failed to get screen dimensions: {e}, using defaults")
            screen_width = 1920
            screen_height = 1080

        # Initialize overlay system
        self.overlay_manager = OverlayManager(event_bus=event_bus)

        # Create and register overlays
        grid_overlay = GridOverlay(
            screen_width=screen_width,
            screen_height=screen_height,
            overlay_manager=self.overlay_manager
        )
        element_overlay = ElementOverlay(
            screen_width=screen_width,
            screen_height=screen_height,
            overlay_manager=self.overlay_manager
        )
        window_overlay = WindowListOverlay(
            screen_width=screen_width,
            screen_height=screen_height,
            overlay_manager=self.overlay_manager
        )
        help_overlay = HelpOverlay(
            screen_width=screen_width,
            screen_height=screen_height,
            overlay_manager=self.overlay_manager
        )
        feedback_overlay = FeedbackOverlay(
            screen_width=screen_width,
            screen_height=screen_height,
            duration=1.5,  # Show for 1.5 seconds
            position="top-right"
        )

        # Register overlays with manager
        self.overlay_manager.register_overlay(OverlayType.GRID, grid_overlay)
        self.overlay_manager.register_overlay(OverlayType.ELEMENT, element_overlay)
        self.overlay_manager.register_overlay(OverlayType.WINDOW, window_overlay)
        self.overlay_manager.register_overlay(OverlayType.HELP, help_overlay)
        self.overlay_manager.register_overlay(OverlayType.FEEDBACK, feedback_overlay)

        # Command context
        self.command_context = CommandContext(
            config=config,
            keyboard_controller=self.keyboard_controller,
            mouse_controller=self.mouse_controller,
            overlay_manager=self.overlay_manager,
            text_processor=text_processor,
            event_bus=event_bus,
            screen_width=screen_width,
            screen_height=screen_height,
        )

        # Subscribe to command execution events for feedback overlay
        self.event_bus.subscribe(EventType.COMMAND_EXECUTED, self._on_command_executed_feedback)

    def _on_command_executed_feedback(self, event: Event) -> None:
        """
        Handle command execution events to show feedback overlay.

        Args:
            event: Command execution event with command_class in data
        """
        try:
            # Get command class name from event
            command_class = event.data.get("command_class", "Command")

            # Skip feedback for overlay commands - they show their own UI
            overlay_commands = [
                "ShowGridCommand",
                "ShowElementsCommand",
                "ShowWindowsCommand",
                "ShowHelpCommand",
                "HideOverlayCommand",
            ]
            if command_class in overlay_commands:
                return

            # Format command name for display (remove "Command" suffix)
            display_name = command_class.replace("Command", "")

            # Add spaces before capital letters for readability
            import re
            display_name = re.sub(r'([A-Z])', r' \1', display_name).strip()

            # Show feedback overlay
            self.overlay_manager.show_overlay(OverlayType.FEEDBACK, text=display_name)

        except Exception as e:
            self.logger.error(f"Error showing command feedback: {e}")

    def _load_whisper_model(self) -> None:
        """Load Whisper model in background."""

        def load():
            try:
                self.model_loading = True
                self.logger.info("Loading Whisper model...")

                model_name = self.config.get("model", "name", default="base.en")
                device = self.config.get("model", "device", default="cpu")
                compute_type = self.config.get("model", "compute_type", default="int8")

                # Auto-detect GPU if device is "auto"
                if device == "auto":
                    try:
                        import torch

                        device = "cuda" if torch.cuda.is_available() else "cpu"
                        self.logger.info(f"Auto-detected device: {device}")
                    except ImportError:
                        device = "cpu"
                        self.logger.info("PyTorch not available, using CPU")

                self.model = WhisperModel(
                    model_name, device=device, compute_type=compute_type
                )

                self.logger.info(f"Whisper model loaded: {model_name} on {device}")
                self.model_loading = False

                self.event_bus.publish(
                    Event(
                        EventType.CONFIG_CHANGED,
                        {
                            "component": "whisper_model",
                            "status": "loaded",
                            "model": model_name,
                            "device": device,
                        },
                    )
                )

            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                self.model_loading = False
                self.event_bus.publish(
                    Event(
                        EventType.ERROR_OCCURRED,
                        {"component": "whisper_model", "error": str(e)},
                    )
                )

        # Load model in background thread
        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def start_recording(self) -> bool:
        """
        Start audio recording.

        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            self.logger.warning("Already recording")
            return False

        try:
            # Play start beep FIRST (before opening stream for faster response)
            if self.config.get("audio", "beep_on_start", default=True):
                frequency = self.config.get("audio", "start_beep_frequency", default=800)
                duration = self.config.get("audio", "start_beep_duration", default=100)
                self.audio_feedback.play_beep(frequency, duration, self.pyaudio)

            # Reset state
            self.audio_frames = []
            self.audio_queue = queue.Queue()
            self.vad.reset()

            # Open audio stream
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback,
            )

            self.is_recording = True
            self.stream.start_stream()

            # Publish event
            self.event_bus.publish(Event(EventType.RECORDING_STARTED, {"timestamp": time.time()}))

            self.logger.info("Recording started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.event_bus.publish(
                Event(EventType.ERROR_OCCURRED, {"component": "audio_capture", "error": str(e)})
            )
            return False

    def stop_recording(self) -> bytes:
        """
        Stop audio recording and return recorded audio.

        Returns:
            Raw audio data as bytes
        """
        if not self.is_recording:
            self.logger.warning("Not recording")
            return b""

        try:
            # Stop stream
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            # Play stop beep
            if self.config.get("audio", "beep_on_stop", default=True):
                frequency = self.config.get("audio", "stop_beep_frequency", default=600)
                duration = self.config.get("audio", "stop_beep_duration", default=100)
                self.audio_feedback.play_beep(frequency, duration, self.pyaudio)

            # Combine audio frames
            audio_data = b"".join(self.audio_frames)

            # Publish event
            self.event_bus.publish(
                Event(
                    EventType.RECORDING_STOPPED,
                    {"timestamp": time.time(), "audio_length": len(audio_data)},
                )
            )

            self.logger.info(f"Recording stopped, captured {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            self.event_bus.publish(
                Event(EventType.ERROR_OCCURRED, {"component": "audio_capture", "error": str(e)})
            )
            return b""

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio stream to capture audio chunks."""
        if self.is_recording:
            self.audio_frames.append(in_data)
            self.event_bus.publish(
                Event(
                    EventType.AUDIO_CHUNK_RECEIVED,
                    {"size": len(in_data), "timestamp": time.time()},
                )
            )
        return (in_data, pyaudio.paContinue)

    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio using Whisper model.

        Args:
            audio_data: Raw audio bytes (16-bit PCM)

        Returns:
            Transcribed text, or None if transcription failed
        """
        if not audio_data:
            self.logger.warning("No audio data to transcribe")
            return None

        if not self.model:
            if self.model_loading:
                self.logger.warning("Model still loading, please wait")
                return None
            else:
                self.logger.error("Whisper model not loaded")
                return None

        try:
            # Publish transcription started event
            self.event_bus.publish(
                Event(
                    EventType.TRANSCRIPTION_STARTED,
                    {"audio_length": len(audio_data), "timestamp": time.time()},
                )
            )

            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            # Transcribe with Whisper
            beam_size = self.config.get("model", "beam_size", default=5)
            vad_filter = self.config.get("model", "vad_filter", default=False)
            language = self.config.get("model", "language", default="en")

            # Initial prompt to bias model toward English vocabulary
            # Helps prevent transcription of similar-sounding words from other languages
            initial_prompt = "This is an English voice command for computer control with numbers, clicks, and navigation."

            segments, info = self.model.transcribe(
                audio_float,
                beam_size=beam_size,
                vad_filter=vad_filter,
                language=language,
                task="transcribe",  # Ensure transcription mode (not translation)
                initial_prompt=initial_prompt,  # Bias toward English
            )

            # Combine segments into full text
            text = " ".join(segment.text for segment in segments).strip()

            # Publish transcription completed event
            self.event_bus.publish(
                Event(
                    EventType.TRANSCRIPTION_COMPLETED,
                    {
                        "text": text,
                        "language": info.language,
                        "language_probability": info.language_probability,
                        "timestamp": time.time(),
                    },
                )
            )

            self.logger.info(f"Transcribed: '{text}'")
            return text

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            self.event_bus.publish(
                Event(
                    EventType.TRANSCRIPTION_FAILED,
                    {"error": str(e), "timestamp": time.time()},
                )
            )
            return None

    def process_text(self, text: str) -> None:
        """
        Process transcribed text through the command system.

        Workflow:
        1. Process text through TextProcessor (punctuation, vocabulary)
        2. Check if command was detected in TextProcessor
        3. If no command, try to match command in CommandRegistry
        4. If no command match, type the processed text
        5. Publish events throughout

        Args:
            text: Transcribed text to process
        """
        if not text:
            return

        try:
            # Process text (punctuation commands, custom vocabulary)
            processed_text, command_action = self.text_processor.process(text)

            # Publish text processed event
            self.event_bus.publish(
                Event(
                    EventType.TEXT_PROCESSED,
                    {
                        "original": text,
                        "processed": processed_text,
                        "command_action": command_action,
                    },
                )
            )

            # Handle command actions from TextProcessor (e.g., "undo_last", "clear_line")
            if command_action:
                self._handle_text_processor_command(command_action)
                return

            # Try to match command in registry
            if processed_text:
                result_text, command_executed = self.command_registry.process(
                    processed_text, self.command_context
                )

                if command_executed:
                    # Command was executed, type any result text if provided
                    self.logger.info(f"✓ Command executed for: '{processed_text}'")
                    print(f"✓ Command executed: {processed_text}")
                    if result_text:
                        self._type_text(result_text)
                else:
                    # No command matched
                    self.logger.info(f"✗ No command matched for: '{processed_text}'")
                    print(f"✗ No command found: {processed_text}")

                    # Check if we should type text or do nothing
                    command_only_mode = self.config.get("text_processing", "command_only_mode", default=True)
                    if not command_only_mode:
                        # Traditional dictation mode: type the processed text
                        self._type_text(processed_text)
                    else:
                        # Command-only mode: do nothing
                        self.logger.info(f"   (command-only mode: ignoring)")

        except Exception as e:
            self.logger.error(f"Error processing text: {e}")
            self.event_bus.publish(
                Event(
                    EventType.ERROR_OCCURRED,
                    {"component": "text_processing", "text": text, "error": str(e)},
                )
            )

    def _handle_text_processor_command(self, command_action: str) -> None:
        """
        Handle commands from TextProcessor (undo_last, clear_line).

        Args:
            command_action: Command action to handle
        """
        if command_action == "undo_last":
            # Delete last typed text
            length = self.text_processor.get_last_text_length()
            for _ in range(length):
                self.keyboard_controller.press(keyboard.Key.backspace)
                self.keyboard_controller.release(keyboard.Key.backspace)

            self.logger.info(f"Undo last: deleted {length} characters")

        elif command_action == "clear_line":
            # Select current line and delete
            self.keyboard_controller.press(keyboard.Key.home)
            self.keyboard_controller.release(keyboard.Key.home)

            with self.keyboard_controller.pressed(keyboard.Key.shift):
                self.keyboard_controller.press(keyboard.Key.end)
                self.keyboard_controller.release(keyboard.Key.end)

            self.keyboard_controller.press(keyboard.Key.backspace)
            self.keyboard_controller.release(keyboard.Key.backspace)

            self.logger.info("Clear line executed")

    def _type_text(self, text: str) -> None:
        """
        Type text using keyboard controller.

        Args:
            text: Text to type
        """
        if not text:
            return

        try:
            self.keyboard_controller.type(text)

            self.event_bus.publish(
                Event(EventType.TEXT_TYPED, {"text": text, "length": len(text)})
            )

            self.logger.info(f"Typed: '{text}'")

        except Exception as e:
            self.logger.error(f"Failed to type text: {e}")
            self.event_bus.publish(
                Event(
                    EventType.ERROR_OCCURRED,
                    {"component": "text_injection", "text": text, "error": str(e)},
                )
            )

    def check_silence(self, silence_threshold: float) -> bool:
        """
        Check if silence duration exceeds threshold.

        Args:
            silence_threshold: Silence duration threshold in seconds

        Returns:
            True if silence duration exceeds threshold
        """
        return self.vad.get_silence_duration() > silence_threshold

    def has_speech(self) -> bool:
        """
        Check if speech has been detected since recording started.

        Returns:
            True if speech was detected
        """
        return self.vad.speech_detected

    def get_audio_duration(self) -> float:
        """
        Get duration of recorded audio in seconds.

        Returns:
            Duration in seconds
        """
        if not self.audio_frames:
            return 0.0

        total_bytes = sum(len(frame) for frame in self.audio_frames)
        bytes_per_second = self.sample_rate * self.channels * 2  # 16-bit = 2 bytes
        return total_bytes / bytes_per_second

    def cleanup(self) -> None:
        """Clean up resources (audio stream, model, etc.)."""
        try:
            # Stop recording if active
            if self.is_recording:
                self.stop_recording()

            # Close audio stream
            if self.stream:
                self.stream.close()
                self.stream = None

            # Terminate PyAudio
            if self.pyaudio:
                self.pyaudio.terminate()
                self.pyaudio = None

            self.logger.info("Dictation engine cleaned up")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
