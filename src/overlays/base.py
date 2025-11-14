"""Base classes for overlay system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple


class OverlayType(Enum):
    """Types of overlays available in the system."""

    GRID = auto()
    ELEMENT = auto()
    WINDOW = auto()
    HELP = auto()
    FEEDBACK = auto()


@dataclass
class OverlayState:
    """
    Tracks the state of an overlay.

    Attributes:
        is_visible: Whether the overlay is currently visible
        overlay_type: Type of the overlay
        element_positions: Map of element numbers to screen positions (x, y)
        metadata: Additional overlay-specific metadata
    """

    is_visible: bool = False
    overlay_type: Optional[OverlayType] = None
    element_positions: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clear(self) -> None:
        """Clear all state (called when overlay is hidden)."""
        self.is_visible = False
        self.overlay_type = None
        self.element_positions.clear()
        self.metadata.clear()

    def get_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get position for a numbered element.

        Args:
            number: Element number

        Returns:
            Tuple of (x, y) pixel coordinates, or None if not found
        """
        return self.element_positions.get(number)

    def set_position(self, number: int, x: int, y: int) -> None:
        """
        Set position for a numbered element.

        Args:
            number: Element number
            x: X coordinate in pixels
            y: Y coordinate in pixels
        """
        self.element_positions[number] = (x, y)

    def has_element(self, number: int) -> bool:
        """
        Check if element number exists.

        Args:
            number: Element number to check

        Returns:
            True if element exists, False otherwise
        """
        return number in self.element_positions


class Overlay(ABC):
    """
    Abstract base class for all overlays.

    Overlays are UI elements that display numbered positions on screen
    for voice-controlled clicking. Examples include grid overlays, UI
    element overlays, and window lists.

    Each overlay must implement:
    1. show() - Display the overlay
    2. hide() - Hide the overlay
    3. is_visible - Property indicating visibility
    4. handle_input(text) - Process voice commands
    5. overlay_type - Property indicating overlay type

    Overlays follow the Strategy pattern, allowing different overlay
    implementations to be swapped at runtime.

    Example:
        ```python
        class GridOverlay(Overlay):
            def show(self, grid_size: int = 9):
                # Create tkinter window with numbered grid
                self._create_grid(grid_size)
                self._visible = True

            def hide(self):
                if self._window:
                    self._window.destroy()
                self._visible = False

            @property
            def is_visible(self) -> bool:
                return self._visible

            @property
            def overlay_type(self) -> OverlayType:
                return OverlayType.GRID
        ```
    """

    @abstractmethod
    def show(self, **kwargs) -> None:
        """
        Show the overlay.

        Args:
            **kwargs: Overlay-specific display options
        """
        pass

    @abstractmethod
    def hide(self) -> None:
        """Hide the overlay and clean up resources."""
        pass

    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """
        Check if overlay is currently visible.

        Returns:
            True if visible, False otherwise
        """
        pass

    @abstractmethod
    def handle_input(self, text: str) -> bool:
        """
        Handle voice input directed at this overlay.

        Args:
            text: Voice command text

        Returns:
            True if input was handled, False otherwise
        """
        pass

    @property
    @abstractmethod
    def overlay_type(self) -> OverlayType:
        """
        Get the type of this overlay.

        Returns:
            OverlayType enum value
        """
        pass

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get position for a numbered element.

        This is a convenience method that overlays can override. The default
        implementation returns None.

        Args:
            number: Element number

        Returns:
            Tuple of (x, y) pixel coordinates, or None if not found
        """
        return None

    def validate_before_show(self) -> bool:
        """
        Validate that overlay can be shown.

        Override this to add pre-show validation (e.g., check dependencies,
        platform requirements, etc.).

        Returns:
            True if overlay can be shown (default), False otherwise
        """
        return True

    def on_show(self) -> None:
        """
        Hook called after overlay is shown.

        Override this to add post-show logic (e.g., publish events,
        update state, etc.).
        """
        pass

    def on_hide(self) -> None:
        """
        Hook called after overlay is hidden.

        Override this to add post-hide logic (e.g., cleanup, publish
        events, update state, etc.).
        """
        pass
