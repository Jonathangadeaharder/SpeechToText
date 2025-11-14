"""Command feedback overlay for visual confirmation."""

import logging
import queue
import threading
import tkinter as tk
from typing import Any, Optional, Tuple

from src.overlays.base import Overlay, OverlayType


class FeedbackOverlay(Overlay):
    """
    Temporary feedback overlay that shows command execution confirmation.

    Displays a small, transparent overlay at the top-right of the screen
    showing the command name. Auto-hides after a short duration (1.5 seconds).

    Example:
        ```python
        overlay = FeedbackOverlay(
            screen_width=1920,
            screen_height=1080
        )

        # Show feedback for a command
        overlay.show(text="Screenshot Command")

        # Hide manually (optional, auto-hides after duration)
        overlay.hide()
        ```
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        duration: float = 1.5,
        position: str = "top-right"
    ):
        """
        Initialize feedback overlay.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            duration: How long to display the feedback (seconds)
            position: Where to position the overlay (top-right, top-left, etc.)
        """
        self.logger = logging.getLogger("FeedbackOverlay")
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.duration = duration
        self.position = position

        # UI state
        self._window: Optional[tk.Tk] = None
        self._visible = False
        self._after_id: Optional[str] = None

        # Thread-safe queue for show/hide commands
        self._command_queue: queue.Queue = queue.Queue()
        self._ui_thread: Optional[threading.Thread] = None
        self._running = False

        # Start the dedicated UI thread
        self._start_ui_thread()

    def _start_ui_thread(self) -> None:
        """Start the dedicated UI thread for this overlay."""
        self._running = True
        self._ui_thread = threading.Thread(target=self._ui_loop, daemon=True)
        self._ui_thread.start()

    def _ui_loop(self) -> None:
        """Main loop for the UI thread. Processes show/hide commands."""
        try:
            # Create root window in this thread
            self._window = tk.Tk()
            self._window.withdraw()  # Start hidden

            # Process commands every 50ms
            def check_queue():
                try:
                    # Non-blocking check for commands
                    while True:
                        try:
                            cmd, data = self._command_queue.get_nowait()

                            if cmd == "show":
                                self._show_internal(data)
                            elif cmd == "hide":
                                self._hide_internal()
                            elif cmd == "stop":
                                self._window.quit()
                                return

                        except queue.Empty:
                            break
                except Exception as e:
                    self.logger.error(f"Error processing command: {e}")

                # Schedule next check
                if self._running:
                    self._window.after(50, check_queue)

            # Start checking queue
            check_queue()

            # Run tkinter main loop in this thread
            self._window.mainloop()

        except Exception as e:
            self.logger.error(f"Error in UI thread: {e}")
        finally:
            self._running = False

    def show(self, **kwargs: Any) -> None:
        """
        Show the feedback overlay with text.

        Thread-safe: Can be called from any thread.

        Args:
            **kwargs: Keyword arguments
                - text: Text to display (default: "Command Executed")
        """
        text = kwargs.get("text", "Command Executed")
        self._command_queue.put(("show", text))

    def _show_internal(self, text: str) -> None:
        """Internal method to show overlay (runs in UI thread)."""
        try:
            # Cancel existing hide timer
            if self._after_id:
                self._window.after_cancel(self._after_id)
                self._after_id = None

            # Update window
            self._update_window(text)
            self._visible = True

            # Schedule auto-hide
            duration_ms = int(self.duration * 1000)
            self._after_id = self._window.after(duration_ms, self._safe_hide)

            self.logger.debug(f"Feedback overlay shown: {text}")

        except Exception as e:
            self.logger.error(f"Error showing overlay: {e}")

    def hide(self) -> None:
        """
        Hide the feedback overlay.

        Thread-safe: Can be called from any thread.
        """
        self._command_queue.put(("hide", None))

    def _hide_internal(self) -> None:
        """Internal method to hide overlay (runs in UI thread)."""
        try:
            # Cancel hide timer
            if self._after_id:
                self._window.after_cancel(self._after_id)
                self._after_id = None

            # Hide window
            self._window.withdraw()
            self._visible = False

            self.logger.debug("Feedback overlay hidden")

        except Exception as e:
            self.logger.error(f"Error hiding overlay: {e}")

    def _safe_hide(self) -> None:
        """Called from after() to auto-hide overlay."""
        self._after_id = None
        self._hide_internal()

    @property
    def is_visible(self) -> bool:
        """Check if overlay is visible."""
        return self._visible and self._window is not None

    def handle_input(self, text: str) -> bool:
        """
        Handle voice input (not used for feedback overlay).

        Args:
            text: Voice command text

        Returns:
            False (feedback overlay doesn't handle input)
        """
        return False

    @property
    def overlay_type(self) -> OverlayType:
        """Get overlay type."""
        return OverlayType.FEEDBACK

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get position for a numbered element (not used for feedback overlay).

        Args:
            number: Element number

        Returns:
            None (feedback overlay doesn't have numbered elements)
        """
        return None

    def _update_window(self, text: str) -> None:
        """
        Update the window with new text (or create if doesn't exist).

        Args:
            text: Text to display
        """
        # Configure window if not already done
        if not hasattr(self, '_window_configured'):
            self._window.overrideredirect(True)  # No title bar or borders
            self._window.attributes("-topmost", True)
            self._window.attributes("-alpha", 0.85)  # Semi-transparent
            self._window.configure(bg="#2d2d2d")

            # Calculate position
            window_width = 300
            window_height = 60
            x, y = self._calculate_position(window_width, window_height)

            # Set window position and size
            self._window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Create frame with border
            self._frame = tk.Frame(
                self._window,
                bg="#2d2d2d",
                highlightbackground="#4CAF50",
                highlightthickness=2,
            )
            self._frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            # Create label with command text
            self._label = tk.Label(
                self._frame,
                font=("Arial", 12, "bold"),
                bg="#2d2d2d",
                fg="#4CAF50",
                padx=15,
                pady=10,
            )
            self._label.pack(fill=tk.BOTH, expand=True)

            self._window_configured = True

        # Update label text
        self._label.config(text=text)

        # Show window
        self._window.deiconify()
        self._window.lift()
        self._window.update()

    def _calculate_position(self, width: int, height: int) -> Tuple[int, int]:
        """
        Calculate window position based on position preference.

        Args:
            width: Window width
            height: Window height

        Returns:
            Tuple of (x, y) coordinates
        """
        padding = 20

        if self.position == "top-right":
            x = self.screen_width - width - padding
            y = padding
        elif self.position == "top-left":
            x = padding
            y = padding
        elif self.position == "bottom-right":
            x = self.screen_width - width - padding
            y = self.screen_height - height - padding
        elif self.position == "bottom-left":
            x = padding
            y = self.screen_height - height - padding
        elif self.position == "center":
            x = (self.screen_width - width) // 2
            y = (self.screen_height - height) // 2
        else:
            # Default to top-right
            x = self.screen_width - width - padding
            y = padding

        return x, y

    def validate_before_show(self) -> bool:
        """Validate that feedback overlay can be shown."""
        # Check screen dimensions are valid
        if self.screen_width <= 0 or self.screen_height <= 0:
            self.logger.error("Invalid screen dimensions")
            return False

        return True

    def cleanup(self) -> None:
        """
        Cleanup and stop the UI thread.

        Should be called when shutting down the application.
        """
        self._running = False
        self._command_queue.put(("stop", None))
        if self._ui_thread and self._ui_thread.is_alive():
            self._ui_thread.join(timeout=2.0)
