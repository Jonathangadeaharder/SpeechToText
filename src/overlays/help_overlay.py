"""Help overlay for displaying available commands."""

import logging
import tkinter as tk
from typing import Any, Optional, Tuple

from src.overlays.base import Overlay, OverlayType


class HelpOverlay(Overlay):
    """
    Help overlay that displays available commands.

    Shows a list of voice commands with descriptions and examples.
    Integrates with CommandRegistry to display registered commands.

    Example:
        ```python
        overlay = HelpOverlay(
            screen_width=1920,
            screen_height=1080,
            command_registry=registry
        )

        # Show help overlay
        overlay.show()

        # Hide help overlay
        overlay.hide()
        ```
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        command_registry: Optional[Any] = None,
        overlay_manager: Optional[Any] = None,
    ):
        """
        Initialize help overlay.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            command_registry: Reference to CommandRegistry for getting help text
            overlay_manager: Reference to OverlayManager for state updates
        """
        self.logger = logging.getLogger("HelpOverlay")
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.command_registry = command_registry
        self.overlay_manager = overlay_manager

        # UI state
        self._window: Optional[tk.Tk] = None
        self._visible = False

    def show(self, **kwargs: Any) -> None:
        """Show the help overlay.

        Args:
            **kwargs: Optional keyword arguments (unused for help overlay)
        """
        # Hide existing window if present
        if self._window:
            self.hide()

        # Create overlay window
        self._create_window()
        self._visible = True

        self.logger.info("Help overlay shown")

    def hide(self) -> None:
        """Hide the help overlay."""
        if self._window:
            try:
                self._window.destroy()
            except Exception as e:
                self.logger.error("Error destroying window: %s", e)
            finally:
                self._window = None

        self._visible = False

        self.logger.info("Help overlay hidden")

    @property
    def is_visible(self) -> bool:
        """Check if overlay is visible."""
        return self._visible and self._window is not None

    def handle_input(self, text: str) -> bool:
        """
        Handle voice input.

        Help overlay can be closed with voice commands like "close help"
        or "hide help".

        Args:
            text: Voice command text

        Returns:
            True if input was handled, False otherwise
        """
        text_lower = text.lower().strip()

        # Check for close/hide commands
        if any(cmd in text_lower for cmd in ["close help", "hide help", "exit help"]):
            self.hide()
            return True

        return False

    @property
    def overlay_type(self) -> OverlayType:
        """Get overlay type."""
        return OverlayType.HELP

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get position for a numbered element (not used for help overlay).

        Args:
            number: Element number

        Returns:
            None (help overlay doesn't have numbered elements)
        """
        return None

    def _create_window(self) -> None:
        """Create the tkinter window with help text."""
        # Create fullscreen window (use Toplevel for additional windows)
        try:
            self._window = tk.Toplevel()
        except tk.TclError:
            # If no Tk instance exists, create one
            self._window = tk.Tk()

        # Set attributes first (before overrideredirect)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", 0.95)  # Almost opaque for readability
        self._window.configure(bg="#1a1a1a")

        # Use geometry to cover screen (instead of -fullscreen with overrideredirect)
        self._window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self._window.overrideredirect(True)  # Remove window decorations

        # Create title
        title_label = tk.Label(
            self._window,
            text="Voice Commands Help",
            font=("Arial", 28, "bold"),
            bg="#1a1a1a",
            fg="white",
        )
        title_label.pack(pady=20)

        # Create scrollable frame for help text
        canvas = tk.Canvas(
            self._window,
            bg="#1a1a1a",
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            self._window,
            orient="vertical",
            command=canvas.yview,
        )

        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Get help text
        help_text = self._get_help_text()

        # Create help content
        self._create_help_content(scrollable_frame, help_text)

        # Pack scrollable elements
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=50)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add close instruction
        instruction_label = tk.Label(
            self._window,
            text="Say 'CLOSE HELP' or press ESC to close",
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="#888888",
        )
        instruction_label.pack(pady=10)

        # Allow window to be closed with Escape
        self._window.bind("<Escape>", lambda e: self.hide())

        # Force window to appear and stay visible
        self._window.deiconify()  # Make sure it's visible
        self._window.lift()  # Bring to front
        self._window.focus_force()  # Force focus
        self._window.update_idletasks()  # Process all pending events
        self._window.update()  # Update the display

        # Keep window alive by scheduling periodic updates
        self._schedule_update()

    def _get_help_text(self) -> str:
        """
        Get help text from command registry or use default.

        Returns:
            Help text string
        """
        if self.command_registry:
            try:
                return self.command_registry.get_help_text(enabled_only=True)
            except Exception as e:
                self.logger.error("Error getting help text from registry: %s", e)

        # Default help text if no registry available
        return self._get_default_help_text()

    def _get_default_help_text(self) -> str:
        """
        Get default help text.

        Returns:
            Default help text string
        """
        return """Available Commands:

MOUSE CONTROL:
• Move Up/Down - Move mouse cursor
  Examples: "move up", "move down"

• Click - Click at current position
  Examples: "click", "right click", "double click"

• Scroll Up/Down/Left/Right - Scroll content
  Examples: "scroll up", "scroll down"

SCREEN OVERLAYS:
• Show Grid - Display numbered grid (9x9)
  Examples: "show grid"

• Show Numbers - Display numbered UI elements
  Examples: "show numbers"

• Show Windows - Display numbered window list
  Examples: "show windows"

• Click [number] - Click numbered element
  Examples: "click 5", "click number 12"

• Refine Grid [number] - Zoom into grid cell
  Examples: "refine grid 45"

• Hide - Close current overlay
  Examples: "hide", "hide grid", "hide numbers"

KEYBOARD:
• Type [text] - Type text
  Examples: "type hello world"

• Press Enter/Space - Press key
  Examples: "click enter", "click space"

WINDOW MANAGEMENT:
• Switch Window - Switch windows (Alt+Tab)
  Examples: "switch window", "switch window 3"

• Maximize/Minimize - Window size
  Examples: "maximize", "minimize"

• Move Window Left/Right - Snap window
  Examples: "move window left", "move window right"

TEXT EDITING:
• Select All - Select all text
  Examples: "select all"

• Copy/Cut/Paste - Clipboard
  Examples: "copy", "cut", "paste"

• Undo/Redo - Edit history
  Examples: "undo", "redo"

Say 'AGENT' before each command to activate voice control.
"""

    def _create_help_content(self, parent: tk.Frame, help_text: str) -> None:
        """
        Create help content widgets.

        Args:
            parent: Parent frame
            help_text: Help text to display
        """
        # Parse help text into sections
        sections = self._parse_help_text(help_text)

        for section_title, section_content in sections:
            # Create section frame
            section_frame = tk.Frame(
                parent,
                bg="#2a2a2a",
                highlightbackground="#444444",
                highlightthickness=1,
            )
            section_frame.pack(fill=tk.X, padx=20, pady=10)

            # Section title
            if section_title:
                title_label = tk.Label(
                    section_frame,
                    text=section_title,
                    font=("Arial", 16, "bold"),
                    bg="#2a2a2a",
                    fg="#ffaa00",
                    anchor="w",
                )
                title_label.pack(fill=tk.X, padx=10, pady=5)

            # Section content
            content_label = tk.Label(
                section_frame,
                text=section_content,
                font=("Courier", 11),
                bg="#2a2a2a",
                fg="white",
                anchor="w",
                justify=tk.LEFT,
            )
            content_label.pack(fill=tk.X, padx=20, pady=5)

    def _parse_help_text(self, help_text: str) -> list:
        """
        Parse help text into sections.

        Args:
            help_text: Raw help text

        Returns:
            List of (section_title, section_content) tuples
        """
        sections = []
        current_section = None
        current_content: list[str] = []

        for line in help_text.split("\n"):
            # Check if line is a section header (all caps, ends with colon)
            if line.strip() and line.strip().isupper() and ":" in line:
                # Save previous section
                if current_section is not None:
                    sections.append((current_section, "\n".join(current_content)))

                # Start new section
                current_section = line.strip()
                current_content = []

            elif line.strip():
                current_content.append(line)

        # Save last section
        if current_section is not None:
            sections.append((current_section, "\n".join(current_content)))
        elif current_content:
            # No sections, just content
            sections.append(("", "\n".join(current_content)))

        return sections

    def validate_before_show(self) -> bool:
        """Validate that help overlay can be shown."""
        # Check screen dimensions are valid
        if self.screen_width <= 0 or self.screen_height <= 0:
            self.logger.error("Invalid screen dimensions")
            return False

        return True

    def set_command_registry(self, command_registry: Optional[Any]) -> None:
        """
        Set the command registry reference.

        Args:
            command_registry: CommandRegistry instance
        """
        self.command_registry = command_registry

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
