"""Element overlay for UI element detection and numbering."""

import importlib.util
import logging
import platform
import queue
import threading
import tkinter as tk
from typing import Any, List, Optional, Tuple

from src.overlays.base import Overlay, OverlayType


class ElementOverlay(Overlay):
    """
    Element overlay that detects and numbers UI elements.

    On Windows, uses UI Automation to detect actual UI elements (buttons,
    links, text fields, etc.). On other platforms or if detection fails,
    falls back to a simple 5x5 grid.

    Example:
        ```python
        overlay = ElementOverlay(screen_width=1920, screen_height=1080)

        # Show numbered UI elements
        overlay.show()

        # Get position of element 5
        x, y = overlay.get_element_position(5)
        ```
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        overlay_manager: Optional[Any] = None,
    ):
        """
        Initialize element overlay.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            overlay_manager: Reference to OverlayManager for state updates
        """
        self.logger = logging.getLogger("ElementOverlay")
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.overlay_manager = overlay_manager

        # UI state
        self._window: Optional[tk.Tk] = None
        self._visible = False

        # Element state
        self._elements: List[Tuple[int, int, int, int]] = []  # (x, y, width, height)
        self._use_ui_automation = self._check_ui_automation_available()

        # Thread-safe queue for show/hide commands
        self._command_queue: queue.Queue = queue.Queue()
        self._ui_thread: Optional[threading.Thread] = None
        self._running = False

        # Start the dedicated UI thread
        self._start_ui_thread()

    def _check_ui_automation_available(self) -> bool:
        """
        Check if Windows UI Automation is available.

        Returns:
            True if pywinauto is available and platform is Windows
        """
        if platform.system() != "Windows":
            self.logger.info("UI Automation not available (not Windows)")
            return False

        if importlib.util.find_spec("pywinauto") is None:
            self.logger.info("UI Automation not available (pywinauto not installed)")
            return False

        self.logger.info("UI Automation available (pywinauto found)")
        return True

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
        Show the element overlay.

        Args:
            **kwargs: Optional keyword arguments
                max_elements: Maximum number of elements to detect/show (default: 50)
        """
        max_elements = kwargs.get('max_elements', 50)
        # Put show command in queue with max_elements parameter
        self._command_queue.put(("show", {"max_elements": max_elements}))

    def hide(self) -> None:
        """Hide the element overlay."""
        # Put hide command in queue
        self._command_queue.put(("hide", None))

    @property
    def is_visible(self) -> bool:
        """Check if overlay is visible."""
        return self._visible and self._window is not None

    def handle_input(self, text: str) -> bool:
        """
        Handle voice input (not used for element overlay).

        Args:
            text: Voice command text

        Returns:
            False (element overlay doesn't process input directly)
        """
        return False

    @property
    def overlay_type(self) -> OverlayType:
        """Get overlay type."""
        return OverlayType.ELEMENT

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get center position for a numbered element.

        Args:
            number: Element number (1-based)

        Returns:
            Tuple of (x, y) pixel coordinates for element center, or None if invalid
        """
        if number < 1 or number > len(self._elements):
            return None

        x, y, width, height = self._elements[number - 1]

        # Return center of element
        center_x = x + width // 2
        center_y = y + height // 2

        return (center_x, center_y)

    def _detect_ui_elements(self, max_elements: int) -> bool:
        """
        Detect UI elements using Windows UI Automation.

        Args:
            max_elements: Maximum number of elements to detect

        Returns:
            True if detection succeeded, False otherwise
        """
        try:
            import ctypes
            from pywinauto import Desktop
            from pywinauto.application import Application

            # Get the actual foreground window handle using Windows API
            try:
                # Use Windows API to get foreground window handle
                hwnd = ctypes.windll.user32.GetForegroundWindow()

                if not hwnd:
                    self.logger.warning("No foreground window found")
                    return False

                # Connect to the specific window by handle
                app = Application(backend="uia").connect(handle=hwnd)
                foreground_window = app.top_window()

                self.logger.debug(f"Connected to foreground window: {foreground_window.window_text()}")

            except Exception as e:
                self.logger.warning(f"Could not get foreground window: {e}")
                return False

            # Find clickable elements
            clickable_types = [
                "Button",
                "Hyperlink",
                "MenuItem",
                "TabItem",
                "CheckBox",
                "RadioButton",
                "Edit",  # Text fields
                "ComboBox",
                "ListItem",
            ]

            elements: List[Tuple[int, int, int, int]] = []

            # Search for elements
            try:
                # Get all descendants
                descendants = foreground_window.descendants()

                for elem in descendants:
                    # Stop if we have enough elements
                    if len(elements) >= max_elements:
                        break

                    try:
                        # Check if element is visible and enabled
                        if not elem.is_visible() or not elem.is_enabled():
                            continue

                        # Check if element is clickable type
                        control_type = elem.element_info.control_type
                        if control_type not in clickable_types:
                            continue

                        # Get bounding rectangle
                        rect = elem.rectangle()

                        # Filter out tiny elements (likely decorative)
                        if rect.width() < 10 or rect.height() < 10:
                            continue

                        # Filter out elements outside screen bounds
                        if (rect.left < 0 or rect.top < 0 or
                            rect.right > self.screen_width or
                            rect.bottom > self.screen_height):
                            continue

                        # Add element
                        elements.append((
                            rect.left,
                            rect.top,
                            rect.width(),
                            rect.height()
                        ))

                    except Exception:
                        # Skip elements that cause errors
                        continue

            except Exception as e:
                self.logger.error("Error enumerating UI elements: %s", e)
                return False

            if not elements:
                self.logger.warning("No UI elements detected")
                return False

            self._elements = elements
            self.logger.info("Detected %d UI elements", len(elements))
            return True

        except Exception as e:
            self.logger.error("UI element detection failed: %s", e)
            return False

    def _use_fallback_grid(self) -> None:
        """Use fallback 5x5 grid when UI Automation is not available."""
        self.logger.info("Using fallback 5x5 grid")

        grid_size = 5
        cell_width = self.screen_width / grid_size
        cell_height = self.screen_height / grid_size

        elements = []

        for row in range(grid_size):
            for col in range(grid_size):
                x = int(col * cell_width)
                y = int(row * cell_height)
                width = int(cell_width)
                height = int(cell_height)

                elements.append((x, y, width, height))

        self._elements = elements

    def _show_internal(self, data: dict) -> None:
        """Internal method to show element overlay (called from UI thread)."""
        max_elements = data.get('max_elements', 50)

        # Clear existing widgets if present
        if self._visible:
            for widget in self._window.winfo_children():
                widget.destroy()

        # Detect UI elements or use fallback
        if self._use_ui_automation:
            success = self._detect_ui_elements(max_elements)
            if not success:
                self.logger.info("UI element detection unavailable, using fallback grid")
                print("Using grid overlay (UI elements not available)")
                self._use_fallback_grid()
            else:
                print(f"Showing {len(self._elements)} UI elements")
        else:
            self._use_fallback_grid()
            print("Using grid overlay")

        # Configure window ONCE (only on first show)
        if not hasattr(self, '_window_configured'):
            # IMPORTANT: Set attributes BEFORE overrideredirect on Windows
            # You cannot set -fullscreen after overrideredirect(True)
            self._window.attributes("-topmost", True)
            self._window.attributes("-alpha", 0.7)  # More visible (70% opacity)
            self._window.configure(bg="black")

            # Use geometry instead of -fullscreen with overrideredirect
            # Set window to cover entire screen
            self._window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

            # Now set overrideredirect to remove decorations
            self._window.overrideredirect(True)

            self._window_configured = True

        # Create canvas for drawing
        canvas = tk.Canvas(
            self._window,
            bg="black",
            highlightthickness=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        # Draw elements and numbers
        positions = {}
        for i, (x, y, width, height) in enumerate(self._elements):
            element_number = i + 1

            # Draw element border
            canvas.create_rectangle(
                x, y, x + width, y + height,
                outline="yellow",
                width=2,
                fill="",
            )

            # Draw element number
            center_x = x + width // 2
            center_y = y + height // 2

            # Background for number (for visibility)
            canvas.create_oval(
                center_x - 20, center_y - 20,
                center_x + 20, center_y + 20,
                fill="red",
                outline="white",
                width=2,
            )

            canvas.create_text(
                center_x, center_y,
                text=str(element_number),
                fill="white",
                font=("Arial", 16, "bold"),
            )

            # Store position
            positions[element_number] = (center_x, center_y)

        # Update positions in manager
        if self.overlay_manager:
            self.overlay_manager.update_element_positions(positions)

        # Allow window to be closed with Escape (for testing)
        self._window.bind("<Escape>", lambda e: self.hide())

        # Show and force window to appear
        self._window.deiconify()  # Show window
        self._window.lift()  # Bring to front
        self._window.focus_force()  # Force focus
        self._window.update()  # Update display

        self._visible = True
        mode = "UI Automation" if self._use_ui_automation else "Fallback Grid"
        self.logger.info("Element overlay shown (%s, %d elements)", mode, len(self._elements))

    def validate_before_show(self) -> bool:
        """Validate that element overlay can be shown."""
        # Check screen dimensions are valid
        if self.screen_width <= 0 or self.screen_height <= 0:
            self.logger.error("Invalid screen dimensions")
            return False

        return True

    def get_element_count(self) -> int:
        """
        Get the number of detected elements.

        Returns:
            Number of elements
        """
        return len(self._elements)

    def is_using_ui_automation(self) -> bool:
        """
        Check if using Windows UI Automation.

        Returns:
            True if using UI Automation, False if using fallback grid
        """
        return self._use_ui_automation and len(self._elements) > 0

    def _hide_internal(self) -> None:
        """Internal method to hide element overlay (called from UI thread)."""
        if self._visible:
            # Clear all widgets
            for widget in self._window.winfo_children():
                widget.destroy()

            # Hide window
            self._window.withdraw()

            self._visible = False
            self._elements.clear()

            self.logger.info("Element overlay hidden")
