#!/usr/bin/env python3
"""
Main application entry point for the Speech-to-Text Dictation Tool.

This module initializes all components, sets up the hotkey listener,
and runs the main application loop.
"""

import importlib.util
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Set

from pynput import keyboard

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.commands.handlers.keyboard_commands import (
    BackspaceCommand,
    ClipboardCommand,
    DeleteLineCommand,
    DeleteWordCommand,
    EnterCommand,
    EscapeCommand,
    RedoCommand,
    SaveCommand,
    SelectAllCommand,
    SpaceCommand,
    TabCommand,
    TypeSymbolCommand,
    TypeTextCommand,
    UndoCommand,
)
from src.commands.handlers.mouse_commands import (
    ClickCommand,
    ClickNumberCommand,
    DoubleClickCommand,
    DragBetweenNumbersCommand,
    MiddleClickCommand,
    MouseMoveCommand,
    MoveToNumberCommand,
    RefineGridCommand,
    RightClickCommand,
    ScrollCommand,
)
from src.commands.handlers.navigation_commands import (
    ArrowKeyCommand,
    PageNavigationCommand,
    HomeEndCommand,
)
from src.commands.handlers.overlay_commands import (
    ShowGridCommand,
    ShowElementsCommand,
    ShowWindowsCommand,
    HideOverlayCommand,
    ShowHelpCommand,
)
from src.commands.handlers.window_commands import (
    MaximizeCommand,
    MinimizeCommand,
    CloseWindowCommand,
    CenterWindowCommand,
    MoveWindowCommand,
    SwitchWindowCommand,
)
from src.commands.handlers.screenshot_commands import (
    ScreenshotCommand,
    ReferenceScreenshotCommand,
)
from src.commands.handlers.custom_commands import load_custom_commands
from src.commands.parser import CommandParser
from src.commands.registry import CommandRegistry
from src.core.config import Config
from src.core.events import EventBus, Event, EventType
from src.dictation_engine import DictationEngine
from src.transcription.text_processor import TextProcessor


# Key mapping for left/right variants
KEY_MAPPING = {
    keyboard.Key.ctrl_l: keyboard.Key.ctrl,
    keyboard.Key.ctrl_r: keyboard.Key.ctrl,
    keyboard.Key.cmd_l: keyboard.Key.cmd,
    keyboard.Key.cmd_r: keyboard.Key.cmd,
    keyboard.Key.shift_l: keyboard.Key.shift,
    keyboard.Key.shift_r: keyboard.Key.shift,
    keyboard.Key.alt_l: keyboard.Key.alt,
    keyboard.Key.alt_r: keyboard.Key.alt,
}


class DictationApp:
    """
    Main application class coordinating all components.

    Manages:
    - Component initialization
    - Hotkey listening
    - Application lifecycle
    - Graceful shutdown
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the dictation application.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        print("Loading configuration...")
        self.config = Config(config_path)

        # Initialize event bus
        self.event_bus = EventBus()

        # Initialize text processor
        self.text_processor = TextProcessor(self.config)

        # Initialize command parser
        self.parser = CommandParser()

        # Initialize command registry and register commands
        self.command_registry = CommandRegistry(self.event_bus)
        self._register_commands()

        # Initialize dictation engine
        print("Initializing dictation engine...")
        self.engine = DictationEngine(
            config=self.config,
            event_bus=self.event_bus,
            command_registry=self.command_registry,
            text_processor=self.text_processor,
            parser=self.parser,
        )

        # Hotkey state
        self.currently_pressed: Set[keyboard.Key] = set()
        self.push_to_talk_keys = self._parse_hotkeys(
            self.config.get("hotkeys", "push_to_talk", default=["ctrl", "cmd"])
        )
        # Allow just F1 key alone as push-to-talk
        self.single_key_push_to_talk = {keyboard.Key.f1}
        self.toggle_continuous_keys = self._parse_hotkeys(
            self.config.get("hotkeys", "toggle_continuous", default=["ctrl", "alt", "c"])
        )

        # Mode state
        self.continuous_mode = self.config.get("continuous_mode", "enabled", default=False)
        self.running = True

        # Keyboard listener
        self.keyboard_listener: Optional[keyboard.Listener] = None

        # Subscribe to events for logging
        self._subscribe_to_events()

        print("Initialization complete")

    def _parse_hotkeys(self, key_names: list[str]) -> Set[keyboard.Key]:
        """
        Convert key names from config to pynput Key objects.

        Args:
            key_names: List of key names from config

        Returns:
            Set of pynput Key objects
        """
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
                    logging.warning(f"Unknown key: {key_name} - {e}")
        return keys

    def _register_commands(self) -> None:
        """Register all available commands with the registry."""
        # Custom commands (loaded from config.yaml)
        # These are registered FIRST so they have priority over built-in commands
        custom_cmds = load_custom_commands(self.config)
        for cmd in custom_cmds:
            self.command_registry.register(cmd)

        # Keyboard commands
        self.command_registry.register(EnterCommand())
        self.command_registry.register(TabCommand())
        self.command_registry.register(EscapeCommand())
        self.command_registry.register(SpaceCommand())
        self.command_registry.register(BackspaceCommand())
        self.command_registry.register(DeleteWordCommand())
        self.command_registry.register(DeleteLineCommand())
        self.command_registry.register(ClipboardCommand())
        self.command_registry.register(SelectAllCommand())
        self.command_registry.register(UndoCommand())
        self.command_registry.register(RedoCommand())
        self.command_registry.register(SaveCommand())
        self.command_registry.register(TypeSymbolCommand())
        self.command_registry.register(TypeTextCommand())

        # Mouse commands
        self.command_registry.register(ClickCommand())
        self.command_registry.register(RightClickCommand())
        self.command_registry.register(DoubleClickCommand())
        self.command_registry.register(MiddleClickCommand())
        self.command_registry.register(ScrollCommand())
        self.command_registry.register(MouseMoveCommand())
        self.command_registry.register(ClickNumberCommand(self.parser))
        self.command_registry.register(MoveToNumberCommand(self.parser))
        self.command_registry.register(DragBetweenNumbersCommand(self.parser))
        self.command_registry.register(RefineGridCommand(self.parser))

        # Navigation commands
        self.command_registry.register(ArrowKeyCommand())
        self.command_registry.register(PageNavigationCommand())
        self.command_registry.register(HomeEndCommand())

        # Window commands
        self.command_registry.register(MaximizeCommand())
        self.command_registry.register(MinimizeCommand())
        self.command_registry.register(CloseWindowCommand())
        self.command_registry.register(CenterWindowCommand())
        self.command_registry.register(MoveWindowCommand())
        self.command_registry.register(SwitchWindowCommand())

        # Overlay commands
        self.command_registry.register(ShowGridCommand())
        self.command_registry.register(ShowElementsCommand())
        self.command_registry.register(ShowWindowsCommand())
        self.command_registry.register(HideOverlayCommand())
        self.command_registry.register(ShowHelpCommand())

        # Screenshot commands
        self.command_registry.register(ScreenshotCommand())
        self.command_registry.register(ReferenceScreenshotCommand())

        logging.info(f"Registered {self.command_registry.get_command_count()} commands")

    def _subscribe_to_events(self) -> None:
        """Subscribe to events for logging and monitoring."""
        self.event_bus.subscribe(EventType.RECORDING_STARTED, self._on_recording_started)
        self.event_bus.subscribe(EventType.RECORDING_STOPPED, self._on_recording_stopped)
        self.event_bus.subscribe(EventType.TRANSCRIPTION_COMPLETED, self._on_transcription_completed)
        self.event_bus.subscribe(EventType.TRANSCRIPTION_FAILED, self._on_transcription_failed)
        self.event_bus.subscribe(EventType.COMMAND_EXECUTED, self._on_command_executed)
        self.event_bus.subscribe(EventType.TEXT_TYPED, self._on_text_typed)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._on_error)

    def _on_recording_started(self, event: Event) -> None:
        """Handle recording started event."""
        logging.info("Recording started")

    def _on_recording_stopped(self, event: Event) -> None:
        """Handle recording stopped event."""
        audio_length = event.data.get("audio_length", 0)
        logging.info(f"Recording stopped (captured {audio_length} bytes)")

    def _on_transcription_completed(self, event: Event) -> None:
        """Handle transcription completed event."""
        text = event.data.get("text", "")
        language = event.data.get("language", "unknown")
        probability = event.data.get("language_probability", 0.0)
        logging.info(f"Transcribed: '{text}' (lang: {language}, prob: {probability:.2f})")
        print(f"Transcribed: {text}")

    def _on_transcription_failed(self, event: Event) -> None:
        """Handle transcription failed event."""
        error = event.data.get("error", "unknown error")
        logging.error(f"Transcription failed: {error}")
        print(f"Transcription failed: {error}")

    def _on_command_executed(self, event: Event) -> None:
        """Handle command executed event."""
        command_class = event.data.get("command_class", "Unknown")
        text = event.data.get("text", "")
        logging.info(f"Command executed: {command_class} with text: '{text}'")
        print(f"  → {command_class}")

    def _on_text_typed(self, event: Event) -> None:
        """Handle text typed event."""
        text = event.data.get("text", "")
        logging.debug(f"Typed text: '{text}'")

    def _on_error(self, event: Event) -> None:
        """Handle error event."""
        component = event.data.get("component", "unknown")
        error = event.data.get("error", "unknown error")
        logging.error(f"Error in {component}: {error}")

    def _on_key_press(self, key: keyboard.Key) -> None:
        """
        Handle key press event.

        Args:
            key: Pressed key
        """
        # Map left/right variants to canonical keys
        key = KEY_MAPPING.get(key, key)

        # Add to currently pressed keys
        self.currently_pressed.add(key)

        # Check for push-to-talk (full combination OR single cmd key)
        if not self.continuous_mode:
            # Check if full combination (Ctrl+Cmd) OR just cmd key alone is pressed
            is_full_combo = self.push_to_talk_keys.issubset(self.currently_pressed)
            is_single_key = self.single_key_push_to_talk.issubset(self.currently_pressed)

            if (is_full_combo or is_single_key) and not self.engine.is_recording:
                self.engine.start_recording()

        # Check for toggle continuous mode
        if self.toggle_continuous_keys.issubset(self.currently_pressed):
            self._toggle_continuous_mode()

    def _on_key_release(self, key: keyboard.Key) -> None:
        """
        Handle key release event.

        Args:
            key: Released key
        """
        # Map left/right variants to canonical keys
        key = KEY_MAPPING.get(key, key)

        # Remove from currently pressed keys
        self.currently_pressed.discard(key)

        # Stop recording on push-to-talk release (if not in continuous mode)
        if not self.continuous_mode:
            # Check if released key is part of push-to-talk (combination or single)
            is_combo_key = key in self.push_to_talk_keys
            is_single_key = key in self.single_key_push_to_talk

            if (is_combo_key or is_single_key) and self.engine.is_recording:
                # Check if any push-to-talk keys (combo or single) are still pressed
                combo_still_pressed = self.push_to_talk_keys.intersection(self.currently_pressed)
                single_still_pressed = self.single_key_push_to_talk.intersection(self.currently_pressed)

                if not combo_still_pressed and not single_still_pressed:
                    self._stop_and_transcribe()

    def _toggle_continuous_mode(self) -> None:
        """Toggle continuous dictation mode."""
        self.continuous_mode = not self.continuous_mode
        status = "enabled" if self.continuous_mode else "disabled"
        print(f"\nContinuous mode {status}")
        logging.info(f"Continuous mode {status}")

        # If disabling continuous mode while recording, stop
        if not self.continuous_mode and self.engine.is_recording:
            self._stop_and_transcribe()

    def _stop_and_transcribe(self) -> None:
        """Stop recording and transcribe in background thread."""
        # Stop recording and get audio data
        audio_data = self.engine.stop_recording()

        # Check minimum audio length
        if not audio_data:
            return

        audio_duration = len(audio_data) / (self.engine.sample_rate * self.engine.channels * 2)
        min_length = self.config.get("continuous_mode", "minimum_audio_length", default=0.5)

        if audio_duration < min_length:
            logging.info(f"Audio too short ({audio_duration:.2f}s < {min_length}s), ignoring")
            return

        # Transcribe in background thread
        def transcribe():
            text = self.engine.transcribe_audio(audio_data)
            if text:
                self.engine.process_text(text)

        thread = threading.Thread(target=transcribe, daemon=True)
        thread.start()

    def _continuous_mode_loop(self) -> None:
        """
        Background loop for continuous mode.

        Monitors silence and automatically stops recording when silence threshold is exceeded.
        """
        while self.running:
            if not self.continuous_mode:
                time.sleep(0.5)
                continue

            if not self.engine.is_recording:
                # Start recording in continuous mode
                self.engine.start_recording()
                time.sleep(0.1)
                continue

            # Check for silence
            silence_threshold = self.config.get("continuous_mode", "silence_threshold", default=2.0)
            if self.engine.check_silence(silence_threshold) and self.engine.has_speech():
                # Auto-stop on silence
                audio_duration = self.engine.get_audio_duration()
                min_length = self.config.get("continuous_mode", "minimum_audio_length", default=0.5)

                if audio_duration >= min_length:
                    logging.info(f"Auto-stopping after {silence_threshold}s of silence")
                    self._stop_and_transcribe()
                else:
                    # Audio too short, just stop without transcribing
                    self.engine.stop_recording()

            time.sleep(0.1)

    def run(self) -> None:
        """Run the main application loop."""
        print("\n" + "=" * 60)
        print("Speech-to-Text Dictation Tool - Refactored Edition")
        print("=" * 60)
        print()
        print("Hotkeys:")
        print(f"  Push-to-talk: {' + '.join(str(k).split('.')[-1] for k in self.push_to_talk_keys)}")
        print(f"  Toggle continuous: {' + '.join(str(k).split('.')[-1] for k in self.toggle_continuous_keys)}")
        print()
        print(f"Commands registered: {self.command_registry.get_command_count()}")
        print()
        print("Ready! Hold hotkey to record, release to transcribe.")
        print("Press Ctrl+C to exit.")
        print("=" * 60)
        print()

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self.keyboard_listener.start()

        # Start continuous mode loop in background
        continuous_thread = threading.Thread(target=self._continuous_mode_loop, daemon=True)
        continuous_thread.start()

        # Main loop - just keep running
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shut down the application."""
        self.running = False

        # Stop keyboard listener
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        # Cleanup engine
        self.engine.cleanup()

        print("Shutdown complete")


def main():
    """Main entry point."""
    # Check if config exists
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("ERROR: config.yaml not found!")
        print("Please ensure config.yaml exists in the current directory.")
        sys.exit(1)

    # Check dependencies
    def check_dependencies() -> bool:
        """Check if required dependencies are available."""
        missing = []
        for module in ['pyaudio', 'numpy', 'yaml', 'faster_whisper', 'pynput']:
            if importlib.util.find_spec(module) is None:
                missing.append(module)

        if missing:
            print(f"ERROR: Missing dependencies: {', '.join(missing)}")
            print("\nPlease install all required packages:")
            print("  pip install pyaudio numpy pyyaml faster-whisper pynput")
            return False
        return True

    if not check_dependencies():
        sys.exit(1)

    # Create and run app
    try:
        app = DictationApp(str(config_path))
        app.run()
    except Exception as e:
        logging.exception("Fatal error")
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
