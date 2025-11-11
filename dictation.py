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
import platform
import re
import sys
import threading
import time
import tkinter as tk
import wave
from typing import Dict, List, Optional, Set

import numpy as np
import pyaudio
import yaml
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw
from pynput import keyboard, mouse
from pystray import Icon, Menu, MenuItem

try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logging.warning("pyautogui not available. Screen segmentation features disabled.")

# --- Key Mapping for Left/Right Variants ---
# Map physical keys to canonical keys (handles left/right variants)
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

    def _setup_logging(self) -> None:
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
        stream = None
        try:
            beep_data = AudioFeedback.generate_beep(frequency, duration)
            stream = pyaudio_instance.open(
                format=pyaudio.paInt16, channels=1, rate=44100, output=True
            )
            stream.write(beep_data)
        except Exception as e:
            logging.warning(f"Failed to play beep: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()


# --- Module 3: Numbered Overlay for Screen Element Segmentation ---


class NumberedOverlay:
    """
    Numbered overlay for screen element segmentation.
    Displays clickable numbered labels on screen for voice control.
    """

    def __init__(self):
        self.logger = logging.getLogger("NumberedOverlay")
        self.root = None
        self.canvas = None
        self.elements = {}  # Maps number -> (x, y, width, height)
        self.labels = []  # List of label widgets
        self.is_visible = False
        self.mode = None  # 'grid' or 'elements'
        self.grid_level = 0  # For hierarchical grid zooming
        self.grid_offset = (0, 0)  # Current grid offset for zooming

    def show_grid(self, subdivisions: int = 3):
        """Show a numbered grid overlay for precision clicking."""
        if not PYAUTOGUI_AVAILABLE:
            print("⚠ PyAutoGUI not available. Install with: pip install pyautogui")
            return

        self._cleanup()

        # Get screen size
        screen_width, screen_height = pyautogui.size()

        # Calculate grid cell size
        cell_width = screen_width // subdivisions
        cell_height = screen_height // subdivisions

        # Create transparent overlay window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.7)
        self.root.config(bg="black")
        self.root.title("Voice Control Grid")

        # Make window click-through on Windows
        if platform.system() == "Windows":
            self.root.attributes("-transparentcolor", "black")

        self.canvas = tk.Canvas(
            self.root, bg="black", highlightthickness=0, width=screen_width, height=screen_height
        )
        self.canvas.pack()

        # Draw grid and create numbered elements
        number = 1
        for row in range(subdivisions):
            for col in range(subdivisions):
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height

                # Draw grid cell border
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline="cyan", width=2, fill="", stipple="gray12"
                )

                # Calculate center position for label
                center_x = x1 + cell_width // 2
                center_y = y1 + cell_height // 2

                # Store element position (center of grid cell)
                self.elements[number] = (center_x, center_y, cell_width, cell_height)

                # Create label with background
                self.canvas.create_oval(
                    center_x - 25,
                    center_y - 25,
                    center_x + 25,
                    center_y + 25,
                    fill="cyan",
                    outline="blue",
                    width=3,
                )
                self.canvas.create_text(
                    center_x,
                    center_y,
                    text=str(number),
                    font=("Arial", 24, "bold"),
                    fill="black",
                )

                number += 1

        self.mode = "grid"
        self.is_visible = True
        print(f"✓ Grid overlay shown with {len(self.elements)} cells")
        print("  Say 'AGENT CLICK [number]' to click a cell")
        print("  Say 'AGENT HIDE NUMBERS' to close")

        # Start mainloop in separate thread
        threading.Thread(target=self.root.mainloop, daemon=True).start()

    def show_numbers(self, max_elements: int = 20):
        """
        Show numbered overlays on clickable screen elements.
        For Phase 2, uses a simple grid-based approach.
        """
        if not PYAUTOGUI_AVAILABLE:
            print("⚠ PyAutoGUI not available. Install with: pip install pyautogui")
            return

        # For now, show a finer grid for more precision
        self.show_grid(subdivisions=5)  # 5x5 grid = 25 elements

    def hide(self):
        """Hide the numbered overlay."""
        self._cleanup()
        print("✓ Overlay hidden")

    def click_element(self, number: int, button: str = "left"):
        """Click on a numbered element."""
        if number not in self.elements:
            print(f"⚠ Element {number} not found")
            return

        x, y, _, _ = self.elements[number]

        # Move mouse and click
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)

        if button == "left":
            pyautogui.click(x, y)
            print(f"✓ Clicked element {number} at ({x}, {y})")
        elif button == "right":
            pyautogui.rightClick(x, y)
            print(f"✓ Right-clicked element {number} at ({x}, {y})")
        elif button == "middle":
            pyautogui.middleClick(x, y)
            print(f"✓ Middle-clicked element {number} at ({x}, {y})")
        elif button == "double":
            pyautogui.doubleClick(x, y)
            print(f"✓ Double-clicked element {number} at ({x}, {y})")

    def _cleanup(self):
        """Clean up overlay resources."""
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass
            self.root = None

        self.canvas = None
        self.elements = {}
        self.labels = []
        self.is_visible = False
        self.mode = None


# --- Module 4: Voice Command Processor ---


class VoiceCommandProcessor:
    """Process voice commands for mouse control and actions."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("VoiceCommandProcessor")
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()

        # Wake word configuration
        self.wake_word = config.get("wake_word", "word", default="agent").lower()
        self.wake_word_enabled = config.get("wake_word", "enabled", default=True)
        self.listening_for_command = False

        # Command tracking for exponential movement
        self.last_command = None
        self.command_count = 0
        self.base_step_size = 50  # Base movement in pixels

        # Get screen dimensions
        self.screen_width, self.screen_height = self._get_screen_size()
        self.logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")

        # Initialize numbered overlay for screen segmentation
        self.overlay = NumberedOverlay()

    def _get_screen_size(self):
        """Get screen dimensions using tkinter."""
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()  # Hide the window
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return width, height
        except Exception as e:
            self.logger.warning(f"Could not get screen size: {e}, using defaults")
            return 1920, 1080  # Default fallback

    def process_command(self, text: str) -> Optional[str]:
        """
        Process voice command or return text for typing.

        Args:
            text: Transcribed text

        Returns:
            Text to type, or None if command was executed
        """
        if not text:
            return None

        text_lower = text.lower().strip()

        # Check for wake word
        if self.wake_word in text_lower and self.wake_word_enabled:
            self.listening_for_command = True
            self.logger.info(f"Wake word '{self.wake_word}' detected!")
            print("🎯 Wake word detected! Listening for command...")

            # Extract command after wake word
            wake_word_index = text_lower.index(self.wake_word)
            command_text = text_lower[wake_word_index + len(self.wake_word) :].strip()
            # Strip leading punctuation (commas, periods, etc.)
            command_text = command_text.lstrip(",.!?;: ")

            if command_text:
                return self._execute_command(command_text)
            return None

        # If we're in command mode but no wake word, treat as command
        if self.listening_for_command:
            return self._execute_command(text_lower)

        # Otherwise, return text for normal typing
        return None

    def _execute_command(self, command: str) -> Optional[str]:
        """Execute a voice command."""
        command = command.strip()

        # Mouse movement commands
        if command.startswith("move"):
            return self._handle_move_command(command)

        # Click commands
        elif command.startswith("click"):
            return self._handle_click_command(command)

        # Type command
        elif command.startswith("type"):
            return self._handle_type_command(command)

        # Window switching commands
        elif "switch window" in command:
            return self._handle_switch_window_command(command)

        # Tab switching commands
        elif "switch tab" in command:
            return self._handle_switch_tab_command(command)

        # Text selection commands
        elif "select" in command:
            return self._handle_select_command(command)

        # Clipboard commands
        elif command in ["copy", "cut", "paste"]:
            return self._handle_clipboard_command(command)

        # Undo/Redo commands
        elif command in ["undo", "redo"]:
            return self._handle_undo_redo_command(command)

        # Navigation commands
        elif "go to" in command:
            return self._handle_navigation_command(command)

        # Deletion commands
        elif "delete" in command or "backspace" in command:
            return self._handle_deletion_command(command)

        # Scrolling commands
        elif "scroll" in command:
            return self._handle_scroll_command(command)

        # Page navigation
        elif "page" in command:
            return self._handle_page_command(command)

        # Overlay commands for screen segmentation
        elif "show numbers" in command or "show elements" in command:
            return self._handle_show_numbers_command()

        elif "show grid" in command:
            return self._handle_show_grid_command()

        elif "hide numbers" in command or "hide grid" in command or "close overlay" in command:
            return self._handle_hide_overlay_command()

        # Click numbered element (must check after other "click" commands)
        elif "click" in command and any(digit in command for digit in "0123456789"):
            return self._handle_click_number_command(command)

        # Unknown command
        else:
            self.logger.warning(f"Unknown command: {command}")
            print(f"⚠ Unknown command: {command}")
            self.listening_for_command = False
            return None

    def _handle_move_command(self, command: str) -> None:
        """Handle mouse movement commands with exponential scaling."""
        # Parse direction
        if "up" in command:
            direction = "up"
        elif "down" in command:
            direction = "down"
        elif "left" in command:
            direction = "left"
        elif "right" in command:
            direction = "right"
        else:
            print("⚠ Invalid move command. Use: MOVE UP/DOWN/LEFT/RIGHT")
            return None

        # Calculate exponential step size
        if self.last_command == f"move {direction}":
            self.command_count += 1
        else:
            self.command_count = 0
            self.last_command = f"move {direction}"

        # Exponential scaling: base * 2^count, capped at 800px
        step_size = min(self.base_step_size * (2**self.command_count), 800)

        # Get current position
        current_x, current_y = self.mouse_controller.position

        # Calculate new position
        new_x, new_y = current_x, current_y

        if direction == "up":
            new_y = max(0, current_y - step_size)
        elif direction == "down":
            new_y = min(self.screen_height - 1, current_y + step_size)
        elif direction == "left":
            new_x = max(0, current_x - step_size)
        elif direction == "right":
            new_x = min(self.screen_width - 1, current_x + step_size)

        # Move mouse
        self.mouse_controller.position = (new_x, new_y)

        multiplier = 2**self.command_count
        print(
            f"🖱️  Moved {direction} by {step_size}px "
            f"(x{multiplier}) → ({int(new_x)}, {int(new_y)})"
        )

    def _handle_click_command(self, command: str) -> None:
        """Handle mouse click commands."""
        if "left" in command:
            self.mouse_controller.click(mouse.Button.left, 1)
            print("🖱️  Left click")
        elif "right" in command:
            self.mouse_controller.click(mouse.Button.right, 1)
            print("🖱️  Right click")
        else:
            print("⚠ Invalid click command. Use: CLICK LEFT or CLICK RIGHT")

        # Reset command tracking after click
        self.last_command = None
        self.command_count = 0

    def _handle_type_command(self, command: str) -> Optional[str]:
        """Handle TYPE command to dictate text."""
        # Extract text after "type"
        type_index = command.find("type")
        if type_index >= 0:
            text_to_type = command[type_index + 4 :].strip()
            if text_to_type:
                print(f"⌨️  Typing: '{text_to_type}'")
                self.listening_for_command = False
                self.last_command = None
                self.command_count = 0
                return text_to_type

        print("⚠ No text specified after TYPE command")
        return None

    def _handle_switch_window_command(self, command: str) -> None:
        """Handle SWITCH WINDOW command to switch between applications."""
        # Parse direction or number
        if "previous" in command or "back" in command:
            # Alt+Shift+Tab for previous window
            print("🪟 Switching to previous window...")
            with self.keyboard_controller.pressed(keyboard.Key.alt):
                with self.keyboard_controller.pressed(keyboard.Key.shift):
                    self.keyboard_controller.press(keyboard.Key.tab)
                    self.keyboard_controller.release(keyboard.Key.tab)
        elif any(digit in command for digit in "0123456789"):
            # Extract number and switch N times
            import re

            numbers = re.findall(r"\d+", command)
            if numbers:
                count = int(numbers[0])
                count = min(count, 20)  # Safety limit
                print(f"🪟 Switching window {count} times...")
                with self.keyboard_controller.pressed(keyboard.Key.alt):
                    for _ in range(count):
                        self.keyboard_controller.press(keyboard.Key.tab)
                        self.keyboard_controller.release(keyboard.Key.tab)
                        time.sleep(0.05)  # Brief delay between presses
        else:
            # Default: next window (Alt+Tab)
            print("🪟 Switching to next window...")
            with self.keyboard_controller.pressed(keyboard.Key.alt):
                self.keyboard_controller.press(keyboard.Key.tab)
                self.keyboard_controller.release(keyboard.Key.tab)

        # Reset command tracking
        self.last_command = None
        self.command_count = 0

    def _handle_switch_tab_command(self, command: str) -> None:
        """Handle SWITCH TAB command to switch between browser/app tabs."""
        # Check for previous/next
        if "previous" in command or "back" in command:
            print("📑 Switching to previous tab...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                with self.keyboard_controller.pressed(keyboard.Key.shift):
                    self.keyboard_controller.press(keyboard.Key.tab)
                    self.keyboard_controller.release(keyboard.Key.tab)
        else:
            # Default: next tab
            print("📑 Switching to next tab...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press(keyboard.Key.tab)
                self.keyboard_controller.release(keyboard.Key.tab)

        # Reset command tracking
        self.last_command = None
        self.command_count = 0

    def _handle_select_command(self, command: str) -> None:
        """Handle text selection commands."""
        if "all" in command:
            print("📝 Selecting all...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press("a")
                self.keyboard_controller.release("a")
        elif "line" in command:
            print("📝 Selecting line...")
            self.keyboard_controller.press(keyboard.Key.home)
            self.keyboard_controller.release(keyboard.Key.home)
            with self.keyboard_controller.pressed(keyboard.Key.shift):
                self.keyboard_controller.press(keyboard.Key.end)
                self.keyboard_controller.release(keyboard.Key.end)
        elif "word" in command:
            print("📝 Selecting word...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                with self.keyboard_controller.pressed(keyboard.Key.shift):
                    self.keyboard_controller.press(keyboard.Key.right)
                    self.keyboard_controller.release(keyboard.Key.right)
        else:
            print("⚠ Unknown select command. Use: SELECT ALL/LINE/WORD")

        self.last_command = None
        self.command_count = 0

    def _handle_clipboard_command(self, command: str) -> None:
        """Handle clipboard commands (copy, cut, paste)."""
        if command == "copy":
            print("📋 Copying...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press("c")
                self.keyboard_controller.release("c")
        elif command == "cut":
            print("✂️  Cutting...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press("x")
                self.keyboard_controller.release("x")
        elif command == "paste":
            print("📋 Pasting...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press("v")
                self.keyboard_controller.release("v")

        self.last_command = None
        self.command_count = 0

    def _handle_undo_redo_command(self, command: str) -> None:
        """Handle undo/redo commands."""
        if command == "undo":
            print("↩️  Undoing...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press("z")
                self.keyboard_controller.release("z")
        elif command == "redo":
            print("↪️  Redoing...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press("y")
                self.keyboard_controller.release("y")

        self.last_command = None
        self.command_count = 0

    def _handle_navigation_command(self, command: str) -> None:
        """Handle navigation commands (go to start/end)."""
        if "start" in command or "top" in command or "beginning" in command:
            print("⬆️  Going to start...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press(keyboard.Key.home)
                self.keyboard_controller.release(keyboard.Key.home)
        elif "end" in command or "bottom" in command:
            print("⬇️  Going to end...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press(keyboard.Key.end)
                self.keyboard_controller.release(keyboard.Key.end)
        elif "line start" in command:
            print("⬅️  Going to line start...")
            self.keyboard_controller.press(keyboard.Key.home)
            self.keyboard_controller.release(keyboard.Key.home)
        elif "line end" in command:
            print("➡️  Going to line end...")
            self.keyboard_controller.press(keyboard.Key.end)
            self.keyboard_controller.release(keyboard.Key.end)
        else:
            print("⚠ Unknown navigation command")

        self.last_command = None
        self.command_count = 0

    def _handle_deletion_command(self, command: str) -> None:
        """Handle deletion commands (delete word, backspace N)."""
        if "word" in command:
            print("🗑️  Deleting word...")
            with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                self.keyboard_controller.press(keyboard.Key.backspace)
                self.keyboard_controller.release(keyboard.Key.backspace)
        elif "backspace" in command:
            # Extract number if present
            import re

            numbers = re.findall(r"\d+", command)
            if numbers:
                count = int(numbers[0])
                count = min(count, 100)  # Safety limit
                print(f"⌫ Backspacing {count} times...")
                for _ in range(count):
                    self.keyboard_controller.press(keyboard.Key.backspace)
                    self.keyboard_controller.release(keyboard.Key.backspace)
            else:
                print("⌫ Backspace...")
                self.keyboard_controller.press(keyboard.Key.backspace)
                self.keyboard_controller.release(keyboard.Key.backspace)
        else:
            print("⚠ Unknown deletion command")

        self.last_command = None
        self.command_count = 0

    def _handle_scroll_command(self, command: str) -> None:
        """Handle scrolling commands with exponential scaling."""
        # Determine direction
        if "up" in command:
            direction = "up"
            scroll_amount = -3
        elif "down" in command:
            direction = "down"
            scroll_amount = 3
        elif "left" in command:
            direction = "left"
            scroll_amount = -3
        elif "right" in command:
            direction = "right"
            scroll_amount = 3
        else:
            print("⚠ Unknown scroll direction. Use: SCROLL UP/DOWN/LEFT/RIGHT")
            return

        # Calculate exponential step size (similar to mouse movement)
        if self.last_command == f"scroll {direction}":
            self.command_count += 1
        else:
            self.command_count = 0
            self.last_command = f"scroll {direction}"

        # Exponential scaling: 3, 6, 12, 24, capped at 48
        multiplier = min(2**self.command_count, 16)
        final_scroll = scroll_amount * multiplier

        print(f"📜 Scrolling {direction} (x{multiplier})...")

        # Perform scroll
        if direction in ["up", "down"]:
            self.mouse_controller.scroll(0, final_scroll)
        else:  # left/right
            self.mouse_controller.scroll(final_scroll, 0)

    def _handle_page_command(self, command: str) -> None:
        """Handle page up/down commands."""
        if "up" in command:
            print("📄 Page up...")
            self.keyboard_controller.press(keyboard.Key.page_up)
            self.keyboard_controller.release(keyboard.Key.page_up)
        elif "down" in command:
            print("📄 Page down...")
            self.keyboard_controller.press(keyboard.Key.page_down)
            self.keyboard_controller.release(keyboard.Key.page_down)
        else:
            print("⚠ Unknown page command. Use: PAGE UP or PAGE DOWN")

        self.last_command = None
        self.command_count = 0

    def _handle_show_numbers_command(self) -> None:
        """Handle SHOW NUMBERS command to display numbered overlay."""
        print("🔢 Showing numbered overlay...")
        self.overlay.show_numbers()
        self.last_command = None
        self.command_count = 0
        return None

    def _handle_show_grid_command(self) -> None:
        """Handle SHOW GRID command to display grid overlay."""
        print("🔢 Showing grid overlay...")
        self.overlay.show_grid(subdivisions=3)
        self.last_command = None
        self.command_count = 0
        return None

    def _handle_hide_overlay_command(self) -> None:
        """Handle HIDE NUMBERS/GRID command to close overlay."""
        print("❌ Hiding overlay...")
        self.overlay.hide()
        self.last_command = None
        self.command_count = 0
        return None

    def _handle_click_number_command(self, command: str) -> None:
        """Handle CLICK [number] commands for numbered overlay elements."""
        # Extract number from command
        numbers = re.findall(r"\d+", command)
        if not numbers:
            print("⚠ No number found in click command")
            return None

        element_number = int(numbers[0])

        # Determine click type
        if "right" in command:
            button = "right"
        elif "middle" in command:
            button = "middle"
        elif "double" in command:
            button = "double"
        else:
            button = "left"

        # Perform click
        self.overlay.click_element(element_number, button=button)

        self.last_command = None
        self.command_count = 0
        return None


# --- Module 5: Text Processor ---


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
        if not self.punctuation_map:
            return text

        # Sort by length descending to avoid partial matches (e.g., "period" before "per")
        words = sorted(self.punctuation_map.keys(), key=len, reverse=True)
        pattern = r"\b(" + "|".join(map(re.escape, words)) + r")\b"

        def repl(match):
            word = match.group(0)
            # Use original case-insensitive mapping
            for k in self.punctuation_map:
                if word.lower() == k.lower():
                    return self.punctuation_map[k]
            return word

        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # Clean up extra spaces around punctuation
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _apply_custom_vocabulary(self, text: str) -> str:
        """Apply custom vocabulary replacements."""
        for phrase, replacement in self.custom_vocabulary.items():
            text = re.sub(r"\b" + re.escape(phrase) + r"\b", replacement, text, flags=re.IGNORECASE)
        return text

    def _execute_command(self, command: str) -> None:
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
            # Use Cmd on macOS, Ctrl on Windows/Linux
            modifier_key = keyboard.Key.cmd if platform.system() == "Darwin" else keyboard.Key.ctrl
            controller.press(modifier_key)
            controller.press(keyboard.Key.backspace)
            controller.release(keyboard.Key.backspace)
            controller.release(modifier_key)
            logging.info("Cleared line")


# --- Module 5: Voice Activity Detector ---


class VoiceActivityDetector:
    """Detect silence/speech using audio energy analysis."""

    def __init__(self, sample_rate: int, chunk_size: int, energy_threshold: float = 0.01):
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

        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        if len(audio_array) == 0:
            return False

        # Calculate RMS (Root Mean Square) energy
        # Use float64 to avoid overflow, then clip to prevent sqrt of negative
        mean_square = np.mean(audio_array.astype(np.float64) ** 2)
        rms = np.sqrt(np.maximum(mean_square, 0))

        # Normalize to 0-1 range (16-bit audio has max value of 32767)
        normalized_rms = rms / 32767.0

        # Detect speech if energy exceeds threshold
        is_speech_detected = normalized_rms > self.energy_threshold

        if is_speech_detected:
            self.last_speech_time = time.time()
            self.speech_detected = True

        return is_speech_detected

    def get_silence_duration(self) -> float:
        """Get duration of silence in seconds since last speech."""
        return time.time() - self.last_speech_time

    def reset(self) -> None:
        """Reset the detector state."""
        self.last_speech_time = time.time()
        self.speech_detected = False


# --- Module 6: Dictation Engine ---


class DictationEngine:
    """Main dictation engine handling recording, transcription, and text injection."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("DictationEngine")

        # State management with thread safety
        self.is_recording = False
        self.recording_lock = threading.Lock()

        # Wake word always listening mode
        self.wake_word_always_listening = config.get("wake_word", "always_listening", default=False)

        # If always listening for wake word, enable continuous mode by default
        self.continuous_mode = (
            config.get("continuous_mode", "enabled", default=False)
            or self.wake_word_always_listening
        )
        self.continuous_mode_lock = threading.Lock()
        self.audio_frames = []
        self.audio_frames_lock = threading.Lock()
        self.currently_pressed = set()
        self.stream = None
        self.running = threading.Event()
        self.running.set()

        # Failure tracking for auto-restart
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        # Initialize components
        self.p = pyaudio.PyAudio()
        self.text_processor = TextProcessor(config)
        self.command_processor = VoiceCommandProcessor(config)
        self.whisper_model = self._load_whisper_model()

        # Audio settings
        self.sample_rate = config.get("audio", "sample_rate", default=16000)
        self.channels = config.get("audio", "channels", default=1)
        self.chunk_size = config.get("audio", "chunk_size", default=1024)
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        self.format = pyaudio.paInt16

        # VAD (Voice Activity Detection) for silence detection
        silence_duration_config = config.get("continuous_mode", "silence_threshold", default=2.0)
        self.silence_duration = silence_duration_config
        self.min_audio_length = config.get("continuous_mode", "minimum_audio_length", default=0.5)
        self.vad = VoiceActivityDetector(self.sample_rate, self.chunk_size, energy_threshold=0.02)
        self.vad_monitor_thread = None
        self.last_audio_chunk = None

        # Hotkeys
        self.push_to_talk_keys = self._parse_hotkeys(
            config.get("hotkeys", "push_to_talk", default=["ctrl", "cmd"])
        )
        self.toggle_continuous_keys = self._parse_hotkeys(
            config.get("hotkeys", "toggle_continuous", default=["ctrl", "shift", "d"])
        )

    def _parse_hotkeys(self, key_names: List[str]) -> Set:
        """Convert key names from config to pynput Key objects."""
        if not key_names:
            raise ValueError("Hotkey list cannot be empty")
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
        with self.recording_lock:
            is_recording = self.is_recording
        if is_recording:
            with self.audio_frames_lock:
                self.audio_frames.append(in_data)
            self.last_audio_chunk = in_data  # Store for VAD monitoring
            return (in_data, pyaudio.paContinue)
        return (in_data, pyaudio.paComplete)

    def _monitor_silence(self):
        """
        Monitor audio for silence in continuous mode.
        Automatically stops recording after silence threshold is exceeded.
        """
        while True:
            with self.recording_lock:
                is_recording = self.is_recording
            with self.continuous_mode_lock:
                continuous_mode = self.continuous_mode

            if not is_recording or not continuous_mode:
                break

            if self.last_audio_chunk:
                # Check if current chunk contains speech
                self.vad.is_speech(self.last_audio_chunk)

                # Get silence duration
                silence_duration = self.vad.get_silence_duration()

                # Calculate total recording duration
                with self.audio_frames_lock:
                    num_frames = len(self.audio_frames)
                recording_duration = (num_frames * self.chunk_size) / self.sample_rate

                # Check if we should auto-stop
                if (
                    self.vad.speech_detected  # We detected speech at some point
                    and silence_duration >= self.silence_duration
                    and recording_duration >= self.min_audio_length
                ):
                    self.logger.info(
                        f"Silence detected for {silence_duration:.1f}s, auto-stopping..."
                    )
                    self.stop_recording()
                    break

            # Check every 100ms
            time.sleep(0.1)

    def start_recording(self):
        """Start recording audio."""
        with self.recording_lock:
            if self.is_recording:
                return
            self.is_recording = True

        with self.audio_frames_lock:
            self.audio_frames = []
        self.last_audio_chunk = None

        # Reset VAD detector
        self.vad.reset()

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

            # Start silence monitoring thread in continuous mode
            with self.continuous_mode_lock:
                continuous_mode = self.continuous_mode
            if continuous_mode:
                self.vad_monitor_thread = threading.Thread(
                    target=self._monitor_silence, daemon=True
                )
                self.vad_monitor_thread.start()
                print("\n🎤 Recording started... (will auto-stop after silence)")
            else:
                print("\n🎤 Recording started...")
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            with self.recording_lock:
                self.is_recording = False
            if self.stream:
                try:
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None

    def stop_recording(self):
        """Stop recording and trigger transcription."""
        with self.recording_lock:
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
        with self.audio_frames_lock:
            frames_copy = self.audio_frames.copy()
        threading.Thread(target=self.transcribe_audio, args=(frames_copy,), daemon=True).start()

    def transcribe_audio(self, frames: List[bytes]):
        """Transcribe audio and inject text."""
        if not frames:
            self.logger.warning("No audio recorded")
            return

        successful = False
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

                # First, check for voice commands (wake word, mouse, etc.)
                command_result = self.command_processor.process_command(text)

                # In always_listening mode, only process if wake word was detected
                wake_word_detected = self.command_processor.listening_for_command or (
                    self.wake_word_always_listening
                    and self.config.get("wake_word", "word", default="agent").lower()
                    in text.lower()
                )

                # If in always_listening mode and no wake word, skip typing
                if self.wake_word_always_listening and not wake_word_detected:
                    print("⏭️  No wake word detected, ignoring...")
                # If command processor returns text OR no command was detected
                elif command_result is not None or not self.command_processor.listening_for_command:
                    text_to_process = command_result if command_result is not None else text
                    processed_text = self.text_processor.process(text_to_process)

                    if processed_text:
                        print("⌨ Typing text...")
                        text_injector = keyboard.Controller()
                        text_injector.type(processed_text)
                        print("✓ Done!\n")
            else:
                print("⚠ Transcription was empty.")

            successful = True

        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            print(f"✗ Error during transcription: {e}")

        finally:
            # Auto-restart recording in continuous mode
            with self.continuous_mode_lock:
                continuous_mode = self.continuous_mode
            if continuous_mode and self.running.is_set():
                if successful:
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.max_consecutive_failures:
                        self.logger.error("Too many consecutive failures, stopping continuous mode")
                        with self.continuous_mode_lock:
                            self.continuous_mode = False
                        return

                time.sleep(0.3)  # Brief pause before restarting
                with self.continuous_mode_lock:
                    continuous_mode = self.continuous_mode
                if continuous_mode:  # Check again in case mode was toggled
                    self.logger.info("Auto-restarting recording in continuous mode...")
                    self.start_recording()

    def toggle_continuous_mode(self):
        """Toggle continuous dictation mode."""
        with self.continuous_mode_lock:
            self.continuous_mode = not self.continuous_mode
            continuous_mode = self.continuous_mode

        if continuous_mode:
            silence_sec = self.silence_duration
            print("\n🔄 Continuous mode ENABLED")
            print(f"   (Speak naturally, auto-transcribes after {silence_sec}s silence)")
            self.start_recording()
        else:
            print("\n🔄 Continuous mode DISABLED")
            print("   (Use push-to-talk hotkey to record)")
            with self.recording_lock:
                is_recording = self.is_recording
            if is_recording:
                self.stop_recording()

    def on_press(self, key):
        """Handle key press events."""
        # Normalize key (map left/right variants to canonical key)
        canonical_key = KEY_MAPPING.get(key, key)

        # Check for push-to-talk
        if canonical_key in self.push_to_talk_keys:
            self.currently_pressed.add(canonical_key)
            with self.continuous_mode_lock:
                continuous_mode = self.continuous_mode
            if self.currently_pressed == self.push_to_talk_keys and not continuous_mode:
                self.start_recording()

        # Check for toggle continuous mode
        if canonical_key in self.toggle_continuous_keys:
            self.currently_pressed.add(canonical_key)
            # Debug: Show what's pressed
            if self.config.get("advanced", "verbose", default=False):
                print(f"Debug: Currently pressed: {self.currently_pressed}")
                print(f"Debug: Expected: {self.toggle_continuous_keys}")
            if self.currently_pressed == self.toggle_continuous_keys:
                self.toggle_continuous_mode()

    def on_release(self, key):
        """Handle key release events."""
        # Normalize key (map left/right variants to canonical key)
        canonical_key = KEY_MAPPING.get(key, key)

        if canonical_key in self.push_to_talk_keys:
            with self.continuous_mode_lock:
                continuous_mode = self.continuous_mode
            with self.recording_lock:
                is_recording = self.is_recording
            if not continuous_mode and is_recording:
                self.stop_recording()
            if canonical_key in self.currently_pressed:
                self.currently_pressed.remove(canonical_key)

        if canonical_key in self.toggle_continuous_keys:
            if canonical_key in self.currently_pressed:
                self.currently_pressed.remove(canonical_key)

    def cleanup(self):
        """Cleanup resources."""
        self.running.clear()
        if self.stream:
            self.stream.close()
        self.p.terminate()


# --- Module 7: System Tray Icon ---


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
        sys.exit(0)

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

    # Check if always listening for wake word
    always_listening = config.get("wake_word", "always_listening", default=False)
    wake_word = config.get("wake_word", "word", default="agent").upper()
    if always_listening:
        print(f"   Wake word always listening: ✓ ('{wake_word}')")

    print("\n" + "=" * 70)
    if always_listening:
        print(f"✓ Ready! Always listening for wake word '{wake_word}'...")
        print(f"   Just say '{wake_word}' followed by your command (no hotkey needed)")
    else:
        print("✓ Ready! Listening for hotkeys...")
    print("=" * 70 + "\n")

    # Start system tray if enabled
    if config.get("system_tray", "enabled", default=True):
        tray_icon = SystemTrayIcon(engine)
        threading.Thread(target=tray_icon.run, daemon=True).start()

    # Auto-start recording if always listening for wake word
    if always_listening:
        print("🎤 Starting always-on listening mode...")
        engine.start_recording()

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
