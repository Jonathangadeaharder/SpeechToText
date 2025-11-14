"""Window list overlay for window switching."""

import importlib.util
import logging
import platform
import tkinter as tk
from typing import Any, Dict, List, Optional, Tuple

from src.overlays.base import Overlay, OverlayType


class WindowListOverlay(Overlay):
    """
    Window list overlay that shows numbered open windows.

    Allows voice-controlled window switching by showing a numbered list
    of all open windows.

    Example:
        ```python
        overlay = WindowListOverlay(screen_width=1920, screen_height=1080)

        # Show numbered window list
        overlay.show()

        # Get window for selection (returns window handle/ID)
        window_info = overlay.get_window_info(3)
        if window_info:
            # Switch to window 3
            overlay.switch_to_window(3)
        ```
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        overlay_manager: Optional[Any] = None,
    ):
        """
        Initialize window list overlay.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            overlay_manager: Reference to OverlayManager for state updates
        """
        self.logger = logging.getLogger("WindowListOverlay")
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.overlay_manager = overlay_manager

        # UI state
        self._window: Optional[tk.Tk] = None
        self._visible = False

        # Window list state
        self._windows: List[Dict] = []  # List of window info dicts

    def show(self, **kwargs: Any) -> None:
        """
        Show the window list overlay.

        Args:
            **kwargs: Optional keyword arguments
                max_windows: Maximum number of windows to show (default: 20)
        """
        max_windows = kwargs.get('max_windows', 20)
        # Hide existing window if present
        if self._window:
            self.hide()

        # Enumerate windows
        self._enumerate_windows(max_windows)

        # Create overlay window
        self._create_window()
        self._visible = True

        self.logger.info("Window list overlay shown (%d windows)", len(self._windows))

    def hide(self) -> None:
        """Hide the window list overlay."""
        if self._window:
            try:
                self._window.destroy()
            except Exception as e:
                self.logger.error("Error destroying window: %s", e)
            finally:
                self._window = None

        self._visible = False
        self._windows.clear()

        self.logger.info("Window list overlay hidden")

    @property
    def is_visible(self) -> bool:
        """Check if overlay is visible."""
        return self._visible and self._window is not None

    def handle_input(self, text: str) -> bool:
        """
        Handle voice input (not used for window overlay).

        Args:
            text: Voice command text

        Returns:
            False (window overlay doesn't process input directly)
        """
        return False

    @property
    def overlay_type(self) -> OverlayType:
        """Get overlay type."""
        return OverlayType.WINDOW

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get position for a numbered window entry.

        Note: This returns the position of the list entry, not the window itself.
        Use get_window_info() to get actual window information.

        Args:
            number: Window number (1-based)

        Returns:
            Tuple of (x, y) pixel coordinates, or None if invalid
        """
        if number < 1 or number > len(self._windows):
            return None

        # Return center of the list entry
        # Entries are vertically stacked
        entry_height = 40
        x = self.screen_width // 2
        y = 100 + (number - 1) * entry_height + entry_height // 2

        return (x, y)

    def _enumerate_windows(self, max_windows: int) -> None:
        """
        Enumerate open windows.

        Args:
            max_windows: Maximum number of windows to enumerate
        """
        windows = []

        try:
            if platform.system() == "Windows":
                windows = self._enumerate_windows_windows(max_windows)
            elif platform.system() == "Linux":
                windows = self._enumerate_windows_linux(max_windows)
            elif platform.system() == "Darwin":
                windows = self._enumerate_windows_macos(max_windows)
            else:
                self.logger.warning("Unsupported platform: %s", platform.system())

        except Exception as e:
            self.logger.error("Error enumerating windows: %s", e)

        self._windows = windows

    def _enumerate_windows_windows(self, max_windows: int) -> List[Dict]:
        """
        Enumerate windows on Windows platform.

        Args:
            max_windows: Maximum number of windows to enumerate

        Returns:
            List of window info dictionaries
        """
        if importlib.util.find_spec("win32gui") is None:
            self.logger.warning("pywin32 not available, cannot enumerate windows")
            return []

        try:
            import win32gui

            windows: List[Dict] = []

            def enum_callback(hwnd, _):
                if len(windows) >= max_windows:
                    return

                # Check if window is visible
                if not win32gui.IsWindowVisible(hwnd):
                    return

                # Get window title
                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return

                # Filter out some system windows
                if title in ["', 'Program Manager", "MSCTFIME UI"]:
                    return

                # Get window class
                class_name = win32gui.GetClassName(hwnd)

                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "class": class_name,
                })

            win32gui.EnumWindows(enum_callback, None)
            return windows

        except Exception as e:
            self.logger.error("Error enumerating Windows windows: %s", e)
            return []

    def _enumerate_windows_linux(self, max_windows: int) -> List[Dict]:
        """
        Enumerate windows on Linux platform.

        Args:
            max_windows: Maximum number of windows to enumerate

        Returns:
            List of window info dictionaries
        """
        try:
            import subprocess

            # Use wmctrl to list windows
            result = subprocess.run(
                ["wmctrl", "-l"],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                self.logger.warning("wmctrl failed")
                return []

            windows: List[Dict] = []
            for line in result.stdout.strip().split("\n"):
                if len(windows) >= max_windows:
                    break

                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id = parts[0]
                    title = parts[3]

                    windows.append({
                        "id": window_id,
                        "title": title,
                    })

            return windows

        except FileNotFoundError:
            self.logger.warning("wmctrl not available, cannot enumerate windows")
            return []
        except Exception as e:
            self.logger.error("Error enumerating Linux windows: %s", e)
            return []

    def _enumerate_windows_macos(self, max_windows: int) -> List[Dict]:
        """
        Enumerate windows on macOS platform.

        Args:
            max_windows: Maximum number of windows to enumerate

        Returns:
            List of window info dictionaries
        """
        # macOS window enumeration would require pyobjc
        # For now, return empty list
        self.logger.warning("macOS window enumeration not yet implemented")
        return []

    def _create_window(self) -> None:
        """Create the tkinter window with numbered window list."""
        # Create fullscreen window (use Toplevel for additional windows)
        try:
            self._window = tk.Toplevel()
        except tk.TclError:
            # If no Tk instance exists, create one
            self._window = tk.Tk()

        # Set attributes first (before overrideredirect)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", 0.9)  # More opaque for readability
        self._window.configure(bg="#1a1a1a")

        # Use geometry to cover screen (instead of -fullscreen with overrideredirect)
        self._window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self._window.overrideredirect(True)  # Remove window decorations

        # Create title
        title_label = tk.Label(
            self._window,
            text="Select Window",
            font=("Arial", 24, "bold"),
            bg="#1a1a1a",
            fg="white",
        )
        title_label.pack(pady=20)

        # Create frame for window list
        list_frame = tk.Frame(self._window, bg="#1a1a1a")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)

        # Add window entries
        positions = {}
        for i, window_info in enumerate(self._windows):
            window_number = i + 1
            title = window_info.get("title", "Unknown")

            # Truncate long titles
            if len(title) > 80:
                title = title[:77] + "..."

            # Create entry frame
            entry_frame = tk.Frame(
                list_frame,
                bg="#2a2a2a",
                highlightbackground="white",
                highlightthickness=2,
            )
            entry_frame.pack(fill=tk.X, pady=5)

            # Number label
            number_label = tk.Label(
                entry_frame,
                text=f"  {window_number}  ",
                font=("Arial", 16, "bold"),
                bg="#3a3a3a",
                fg="yellow",
            )
            number_label.pack(side=tk.LEFT, padx=5, pady=5)

            # Title label
            title_label = tk.Label(
                entry_frame,
                text=title,
                font=("Arial", 14),
                bg="#2a2a2a",
                fg="white",
                anchor="w",
            )
            title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

            # Store position (center of entry)
            positions[window_number] = (
                self.screen_width // 2,
                100 + i * 40 + 20
            )

        # Add instruction
        instruction_label = tk.Label(
            self._window,
            text="Say 'SWITCH WINDOW [number]' to select",
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="#888888",
        )
        instruction_label.pack(pady=10)

        # Update positions in manager
        if self.overlay_manager:
            self.overlay_manager.update_element_positions(positions)

        # Allow window to be closed with Escape (for testing)
        self._window.bind("<Escape>", lambda e: self.hide())

        # Force window to appear and stay visible
        self._window.deiconify()  # Make sure it's visible
        self._window.lift()  # Bring to front
        self._window.focus_force()  # Force focus
        self._window.update_idletasks()  # Process all pending events
        self._window.update()  # Update the display

        # Keep window alive by scheduling periodic updates
        self._schedule_update()

    def validate_before_show(self) -> bool:
        """Validate that window list can be shown."""
        # Check screen dimensions are valid
        if self.screen_width <= 0 or self.screen_height <= 0:
            self.logger.error("Invalid screen dimensions")
            return False

        return True

    def get_window_info(self, number: int) -> Optional[Dict]:
        """
        Get window information for a numbered entry.

        Args:
            number: Window number (1-based)

        Returns:
            Dictionary with window information, or None if invalid
        """
        if number < 1 or number > len(self._windows):
            return None

        return self._windows[number - 1]

    def switch_to_window(self, number: int) -> bool:
        """
        Switch to a numbered window.

        Args:
            number: Window number (1-based)

        Returns:
            True if switch succeeded, False otherwise
        """
        window_info = self.get_window_info(number)
        if not window_info:
            return False

        try:
            if platform.system() == "Windows":
                return self._switch_to_window_windows(window_info)
            elif platform.system() == "Linux":
                return self._switch_to_window_linux(window_info)
            elif platform.system() == "Darwin":
                return self._switch_to_window_macos(window_info)

        except Exception as e:
            self.logger.error("Error switching to window: %s", e)

        return False

    def _switch_to_window_windows(self, window_info: Dict) -> bool:
        """Switch to window on Windows."""
        try:
            import win32gui

            hwnd = window_info.get("hwnd")
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                return True

        except Exception as e:
            self.logger.error("Error switching to Windows window: %s", e)

        return False

    def _switch_to_window_linux(self, window_info: Dict) -> bool:
        """Switch to window on Linux."""
        try:
            import subprocess

            window_id = window_info.get("id")
            if window_id:
                subprocess.run(
                    ["wmctrl", "-i", "-a", window_id],
                    check=False,
                    timeout=2,
                )
                return True

        except Exception as e:
            self.logger.error("Error switching to Linux window: %s", e)

        return False

    def _switch_to_window_macos(self, window_info: Dict) -> bool:
        """Switch to window on macOS."""
        # macOS implementation would require pyobjc
        self.logger.warning("macOS window switching not yet implemented")
        return False

    def get_window_count(self) -> int:
        """
        Get the number of windows in the list.

        Returns:
            Number of windows
        """
        return len(self._windows)

    def _schedule_update(self) -> None:
        """Schedule periodic updates to keep window alive."""
        if self._window and self._visible:
            try:
                self._window.update()
                # Schedule next update in 100ms
                self._window.after(100, self._schedule_update)
            except Exception:
                # Window was destroyed
                pass
