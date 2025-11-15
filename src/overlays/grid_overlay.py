"""Grid overlay for screen segmentation."""

import logging
import queue
import threading
import tkinter as tk
from datetime import datetime
from typing import Any, Optional, Tuple

from src.overlays.base import Overlay, OverlayType

# Setup file logging for debugging
import os
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'grid_overlay_debug.log')
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
grid_logger = logging.getLogger("GridOverlay")
grid_logger.addHandler(file_handler)
grid_logger.setLevel(logging.DEBUG)


class GridOverlay(Overlay):
    """
    Grid overlay that divides the screen into numbered cells.

    Supports multiple grid sizes (3x3, 5x5, 9x9) and can refine/zoom
    into individual cells for more precise clicking.

    Example:
        ```python
        overlay = GridOverlay(screen_width=1920, screen_height=1080)

        # Show 9x9 grid (81 cells)
        overlay.show(grid_size=9)

        # Get position of cell 45
        x, y = overlay.get_element_position(45)

        # Refine/zoom into cell 45 with 3x3 subdivision
        overlay.refine_grid(45)

        # Now cells 1-9 are subdivisions of the original cell 45
        x, y = overlay.get_element_position(5)  # Center of cell 45

        # Reset to full grid
        overlay.show(grid_size=9)
        ```
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        overlay_manager: Optional[Any] = None,
    ):
        """
        Initialize grid overlay.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            overlay_manager: Reference to OverlayManager for state updates
        """
        self.logger = grid_logger  # Use file logger
        self.logger.info("=" * 80)
        self.logger.info(f"GridOverlay initializing - screen: {screen_width}x{screen_height}")
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.overlay_manager = overlay_manager

        # UI state
        self._window: Optional[tk.Tk] = None
        self._visible = False

        # Grid state
        self._grid_size = 9  # Default to 9x9
        self._current_bounds = None  # None = full screen, otherwise (x, y, width, height)
        self._refined_cell = None  # Which cell was refined

        # Thread-safe queue for show/hide commands
        self._command_queue: queue.Queue = queue.Queue()
        self._ui_thread: Optional[threading.Thread] = None
        self._running = False

        self.logger.info("Starting dedicated UI thread...")
        # Start the dedicated UI thread
        self._start_ui_thread()
        self.logger.info("GridOverlay initialization complete")

    def _start_ui_thread(self) -> None:
        """Start the dedicated UI thread for this overlay."""
        self.logger.info("_start_ui_thread() called")
        self._running = True
        self._ui_thread = threading.Thread(target=self._ui_loop, daemon=True)
        self._ui_thread.start()
        self.logger.info(f"UI thread started: {self._ui_thread.name}")

    def _ui_loop(self) -> None:
        """Main loop for the UI thread. Processes show/hide commands."""
        try:
            self.logger.info("UI thread starting...")
            print(f"[GRID DEBUG] UI thread starting...")
            # Create root window in this thread
            self._window = tk.Tk()
            self.logger.info("Root window created")
            self._window.withdraw()  # Start hidden
            self.logger.info("Root window withdrawn (hidden)")
            print(f"[GRID DEBUG] Root window created and withdrawn")

            # Process commands every 50ms
            def check_queue():
                try:
                    # Non-blocking check for commands
                    while True:
                        try:
                            cmd, data = self._command_queue.get_nowait()
                            self.logger.info(f"Queue: Got command '{cmd}' with data: {data}")
                            print(f"[GRID DEBUG] Processing command: {cmd}")

                            if cmd == "show":
                                self.logger.info("Calling _show_internal()")
                                self._show_internal(data)
                            elif cmd == "hide":
                                self.logger.info("Calling _hide_internal()")
                                self._hide_internal()
                            elif cmd == "refine":
                                self.logger.info("Calling _refine_internal()")
                                self._refine_internal(data)
                            elif cmd == "stop":
                                self.logger.info("Stopping UI thread (quit mainloop)")
                                self._window.quit()
                                return

                        except queue.Empty:
                            break
                except Exception as e:
                    self.logger.error(f"Error processing command: {e}", exc_info=True)
                    print(f"[GRID DEBUG] Error processing command: {e}")

                # Schedule next check
                if self._running:
                    self._window.after(50, check_queue)

            # Start checking queue
            self.logger.info("Starting queue checker (scheduling first check)")
            print(f"[GRID DEBUG] Starting queue checker")
            check_queue()

            # Run tkinter main loop in this thread
            self.logger.info("Entering mainloop()")
            print(f"[GRID DEBUG] Entering mainloop")
            self._window.mainloop()
            self.logger.info("Mainloop exited")
            print(f"[GRID DEBUG] Mainloop exited")

        except Exception as e:
            self.logger.error(f"Error in UI thread: {e}")
            print(f"[GRID DEBUG] UI thread error: {e}")
        finally:
            self._running = False
            print(f"[GRID DEBUG] UI thread stopped")

    def show(self, **kwargs: Any) -> None:
        """
        Show the grid overlay.

        Args:
            **kwargs: Optional keyword arguments
                grid_size: Size of the grid (e.g., 3 for 3x3, 9 for 9x9) (default: 9)
        """
        grid_size = kwargs.get('grid_size', 9)
        self.logger.info(f"show() called with grid_size={grid_size}")
        self.logger.info(f"  UI thread running: {self._running}")
        self.logger.info(f"  Window exists: {self._window is not None}")
        self.logger.info(f"  Queue size: {self._command_queue.qsize()}")
        print(f"[GRID DEBUG] show() called with grid_size={grid_size}")
        print(f"[GRID DEBUG] UI thread running: {self._running}")
        print(f"[GRID DEBUG] Window exists: {self._window is not None}")
        # Put show command in queue with grid_size parameter
        self._command_queue.put(("show", {"grid_size": grid_size}))
        self.logger.info(f"Show command queued, new queue size: {self._command_queue.qsize()}")
        print(f"[GRID DEBUG] Show command queued")

    def hide(self) -> None:
        """Hide the grid overlay."""
        # Put hide command in queue
        self._command_queue.put(("hide", None))

    @property
    def is_visible(self) -> bool:
        """Check if overlay is visible."""
        return self._visible and self._window is not None

    def handle_input(self, text: str) -> bool:
        """
        Handle voice input (not used for grid overlay).

        Args:
            text: Voice command text

        Returns:
            False (grid overlay doesn't process input directly)
        """
        return False

    @property
    def overlay_type(self) -> OverlayType:
        """Get overlay type."""
        return OverlayType.GRID

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get center position for a grid cell.

        Args:
            number: Cell number (1-based)

        Returns:
            Tuple of (x, y) pixel coordinates for cell center, or None if invalid
        """
        if number < 1 or number > self._grid_size * self._grid_size:
            return None

        # Calculate cell boundaries
        bounds = self._current_bounds or (0, 0, self.screen_width, self.screen_height)
        x_offset, y_offset, width, height = bounds

        cell_width = width / self._grid_size
        cell_height = height / self._grid_size

        # Convert 1-based number to 0-based row/col
        cell_index = number - 1
        row = cell_index // self._grid_size
        col = cell_index % self._grid_size

        # Calculate center of cell
        center_x = int(x_offset + (col + 0.5) * cell_width)
        center_y = int(y_offset + (row + 0.5) * cell_height)

        return (center_x, center_y)

    def refine_grid(self, cell_number: int) -> bool:
        """
        Refine/zoom into a specific cell with 3x3 subdivision.

        After refinement, the grid shows 9 cells (1-9) that subdivide
        the selected cell.

        Args:
            cell_number: Cell number to refine (1-based)

        Returns:
            True if refinement succeeded, False if invalid cell
        """
        # Validate cell number
        if cell_number < 1 or cell_number > self._grid_size * self._grid_size:
            self.logger.warning("Invalid cell number for refinement: %d", cell_number)
            return False

        # Queue refine command for UI thread
        self._command_queue.put(("refine", {"cell_number": cell_number}))
        self.logger.info(f"Refine command queued for cell {cell_number}")
        return True

    def _show_internal(self, data: dict) -> None:
        """Internal method to show grid (called from UI thread)."""
        self.logger.info("_show_internal() called")
        print(f"[GRID DEBUG] _show_internal() called")
        grid_size = data.get('grid_size', 9)
        self.logger.info(f"  grid_size: {grid_size}")

        # Reset to full screen when showing
        self._current_bounds = None
        self._refined_cell = None
        self._grid_size = grid_size
        self.logger.info("Grid state reset to full screen")

        # Clear existing widgets if present
        if self._visible:
            self.logger.info("Clearing existing widgets (grid already visible)")
            print(f"[GRID DEBUG] Clearing existing widgets")
            for widget in self._window.winfo_children():
                widget.destroy()
        else:
            self.logger.info("No existing widgets to clear (first show)")

        # Configure window ONCE (only on first show)
        if not hasattr(self, '_window_configured'):
            self.logger.info("Configuring window for first time...")
            print(f"[GRID DEBUG] Configuring window for first time")

            # IMPORTANT: Set attributes BEFORE overrideredirect on Windows
            # You cannot set -fullscreen after overrideredirect(True)
            self._window.attributes("-topmost", True)
            self.logger.info("  topmost attribute set")
            self._window.attributes("-alpha", 0.7)  # More visible (70% opacity)
            self.logger.info("  alpha=0.7 set")
            self._window.configure(bg="black")
            self.logger.info("  bg=black configured")

            # Use geometry instead of -fullscreen with overrideredirect
            # Set window to cover entire screen
            self._window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
            self.logger.info(f"  geometry set to {self.screen_width}x{self.screen_height}+0+0")

            # Now set overrideredirect to remove decorations
            self._window.overrideredirect(True)
            self.logger.info("  overrideredirect(True) done")

            self._window_configured = True
            self.logger.info("Window configuration COMPLETE")
            print(f"[GRID DEBUG] Window configured")
        else:
            self.logger.info("Window already configured, skipping configuration")
            print(f"[GRID DEBUG] Window already configured")

        # Create canvas for drawing
        canvas = tk.Canvas(
            self._window,
            bg="black",
            highlightthickness=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        # Get grid bounds
        bounds = self._current_bounds or (0, 0, self.screen_width, self.screen_height)
        x_offset, y_offset, width, height = bounds

        cell_width = width / self._grid_size
        cell_height = height / self._grid_size

        # Draw grid and numbers
        positions = {}
        for row in range(self._grid_size):
            for col in range(self._grid_size):
                # Calculate cell position
                x1 = x_offset + col * cell_width
                y1 = y_offset + row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height

                # Draw cell border
                canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="white",
                    width=2,
                    fill="",
                )

                # Calculate cell number (1-based, left-to-right, top-to-bottom)
                cell_number = row * self._grid_size + col + 1

                # Draw cell number in center
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                canvas.create_text(
                    center_x, center_y,
                    text=str(cell_number),
                    fill="white",
                    font=("Arial", 24, "bold"),
                )

                # Store position for later retrieval
                positions[cell_number] = (int(center_x), int(center_y))

        # Update positions in manager
        if self.overlay_manager:
            self.overlay_manager.update_element_positions(positions)

        # Allow window to be closed with Escape (for testing)
        self._window.bind("<Escape>", lambda e: self.hide())

        # Show and force window to appear
        self.logger.info("About to show window...")
        print(f"[GRID DEBUG] About to show window (deiconify)")
        self._window.deiconify()  # Show window
        self.logger.info("  deiconify() done")
        print(f"[GRID DEBUG] Window deiconified, lifting to front")
        self._window.lift()  # Bring to front
        self.logger.info("  lift() done")
        self._window.focus_force()  # Force focus
        self.logger.info("  focus_force() done")
        self._window.update()  # Update display
        self.logger.info("  update() done - window should be visible now")
        print(f"[GRID DEBUG] Window updated, should be visible now")

        self._visible = True
        self.logger.info(f"✓ Grid overlay shown: {grid_size}x{grid_size} - _visible={self._visible}")
        print(f"[GRID DEBUG] Grid overlay shown: {grid_size}x{grid_size}")
        self.logger.info("=" * 40)

    def validate_before_show(self) -> bool:
        """Validate that grid can be shown."""
        # Check screen dimensions are valid
        if self.screen_width <= 0 or self.screen_height <= 0:
            self.logger.error("Invalid screen dimensions")
            return False

        return True

    def get_current_grid_size(self) -> int:
        """
        Get the current grid size.

        Returns:
            Current grid size (e.g., 3, 5, 9)
        """
        return self._grid_size

    def is_refined(self) -> bool:
        """
        Check if grid is currently in refined mode.

        Returns:
            True if grid is zoomed into a cell, False if showing full screen
        """
        return self._current_bounds is not None

    def get_refined_cell(self) -> Optional[int]:
        """
        Get the cell number that was refined.

        Returns:
            Cell number that was refined, or None if not in refined mode
        """
        return self._refined_cell

    def _refine_internal(self, data: dict) -> None:
        """Internal method to refine grid (called from UI thread)."""
        cell_number = data.get("cell_number")
        if not cell_number:
            return

        self.logger.info(f"_refine_internal() called for cell {cell_number}")

        # Calculate cell boundaries
        bounds = self._current_bounds or (0, 0, self.screen_width, self.screen_height)
        x_offset, y_offset, width, height = bounds

        cell_width = width / self._grid_size
        cell_height = height / self._grid_size

        # Convert 1-based number to 0-based row/col
        cell_index = cell_number - 1
        row = cell_index // self._grid_size
        col = cell_index % self._grid_size

        # Calculate bounds of the cell
        cell_x = int(x_offset + col * cell_width)
        cell_y = int(y_offset + row * cell_height)
        cell_w = int(cell_width)
        cell_h = int(cell_height)

        # Update state for refinement
        self._current_bounds = (cell_x, cell_y, cell_w, cell_h)
        self._refined_cell = cell_number
        self._grid_size = 3  # Always use 3x3 for refinement

        # Clear existing widgets
        if self._visible:
            for widget in self._window.winfo_children():
                widget.destroy()

        # Redraw grid with new bounds
        canvas = tk.Canvas(
            self._window,
            bg="black",
            highlightthickness=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        # Get refined grid bounds
        x_offset, y_offset, width, height = self._current_bounds

        cell_width = width / self._grid_size
        cell_height = height / self._grid_size

        # Draw refined grid and numbers
        positions = {}
        for row in range(self._grid_size):
            for col in range(self._grid_size):
                # Calculate cell position
                x1 = x_offset + col * cell_width
                y1 = y_offset + row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height

                # Draw cell border
                canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="white",
                    width=2,
                    fill="",
                )

                # Calculate cell number (1-based, left-to-right, top-to-bottom)
                cell_num = row * self._grid_size + col + 1

                # Draw cell number in center
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                canvas.create_text(
                    center_x, center_y,
                    text=str(cell_num),
                    fill="white",
                    font=("Arial", 24, "bold"),
                )

                # Store position for later retrieval
                positions[cell_num] = (int(center_x), int(center_y))

        # Update positions in manager
        if self.overlay_manager:
            self.overlay_manager.update_element_positions(positions)
            self.overlay_manager.set_metadata("refined_cell", cell_number)

        # Allow window to be closed with Escape (for testing)
        self._window.bind("<Escape>", lambda e: self.hide())

        self._visible = True
        self.logger.info(f"✓ Grid refined to cell {cell_number} (3x3)")

    def _hide_internal(self) -> None:
        """Internal method to hide grid (called from UI thread)."""
        if self._visible:
            # Clear all widgets
            for widget in self._window.winfo_children():
                widget.destroy()

            # Hide window
            self._window.withdraw()

            self._visible = False
            self._current_bounds = None
            self._refined_cell = None

            self.logger.info("Grid overlay hidden")
