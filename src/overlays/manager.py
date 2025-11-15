"""Overlay manager for coordinating multiple overlays."""

import logging
from typing import Any, Dict, Optional, Tuple

from src.core.events import Event, EventBus, EventType
from src.overlays.base import Overlay, OverlayState, OverlayType


class OverlayManager:
    """
    Manages multiple overlays and coordinates their display.

    The OverlayManager:
    1. Registers overlay instances by type
    2. Shows/hides overlays, ensuring only one is visible at a time
    3. Tracks current overlay state
    4. Publishes overlay lifecycle events via event bus
    5. Provides element position lookup for click commands

    Example:
        ```python
        manager = OverlayManager(event_bus)

        # Register overlays
        manager.register_overlay(OverlayType.GRID, grid_overlay)
        manager.register_overlay(OverlayType.ELEMENT, element_overlay)

        # Show an overlay
        manager.show_overlay(OverlayType.GRID, grid_size=9)

        # Get element position for clicking
        position = manager.get_element_position(5)
        if position:
            x, y = position
            # Click at position

        # Hide overlay
        manager.hide_current_overlay()
        ```
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the overlay manager.

        Args:
            event_bus: Optional event bus for publishing overlay events
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger("OverlayManager")
        self._overlays: Dict[OverlayType, Overlay] = {}
        self._current_overlay: Optional[Overlay] = None
        self._state = OverlayState()

    def register_overlay(self, overlay_type: OverlayType, overlay: Overlay) -> None:
        """
        Register an overlay implementation.

        Args:
            overlay_type: Type of overlay
            overlay: Overlay instance to register
        """
        self._overlays[overlay_type] = overlay
        self.logger.debug("Registered overlay: %s", overlay_type.name)

    def unregister_overlay(self, overlay_type: OverlayType) -> bool:
        """
        Unregister an overlay.

        Args:
            overlay_type: Type of overlay to unregister

        Returns:
            True if overlay was found and removed, False otherwise
        """
        if overlay_type in self._overlays:
            # Hide the overlay if it's currently visible
            if self._current_overlay == self._overlays[overlay_type]:
                self.hide_current_overlay()

            del self._overlays[overlay_type]
            self.logger.debug("Unregistered overlay: %s", overlay_type.name)
            return True
        return False

    def show_overlay(self, overlay_type: OverlayType, **kwargs) -> bool:
        """
        Show an overlay, hiding any currently visible overlay.

        Args:
            overlay_type: Type of overlay to show
            **kwargs: Overlay-specific display options

        Returns:
            True if overlay was shown successfully, False otherwise
        """
        # Check if overlay is registered
        if overlay_type not in self._overlays:
            self.logger.warning("Overlay not registered: %s", overlay_type.name)
            return False

        overlay = self._overlays[overlay_type]

        # Validate before showing
        if not overlay.validate_before_show():
            self.logger.warning("Overlay validation failed: %s", overlay_type.name)
            return False

        # Hide current overlay if different
        if self._current_overlay and self._current_overlay != overlay:
            self.hide_current_overlay()

        # Show the new overlay
        try:
            overlay.show(**kwargs)
            self._current_overlay = overlay
            self._state.is_visible = True
            self._state.overlay_type = overlay_type

            # Call post-show hook
            overlay.on_show()

            # Publish event
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        EventType.OVERLAY_SHOWN,
                        {
                            "overlay_type": overlay_type.name,
                            "kwargs": kwargs,
                        }
                    )
                )

            self.logger.info("Overlay shown: %s", overlay_type.name)
            return True

        except Exception as e:
            self.logger.error("Error showing overlay %s: %s", overlay_type.name, e)
            return False

    def hide_overlay(self, overlay_type: OverlayType) -> bool:
        """
        Hide a specific overlay.

        Args:
            overlay_type: Type of overlay to hide

        Returns:
            True if overlay was hidden, False if not found or not visible
        """
        if overlay_type not in self._overlays:
            return False

        overlay = self._overlays[overlay_type]

        # Only hide if it's currently visible
        if self._current_overlay != overlay:
            return False

        try:
            overlay.hide()

            # Call post-hide hook
            overlay.on_hide()

            # Clear state
            self._state.clear()
            self._current_overlay = None

            # Publish event
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        EventType.OVERLAY_HIDDEN,
                        {"overlay_type": overlay_type.name}
                    )
                )

            self.logger.info("Overlay hidden: %s", overlay_type.name)
            return True

        except Exception as e:
            self.logger.error("Error hiding overlay %s: %s", overlay_type.name, e)
            return False

    def hide_current_overlay(self) -> bool:
        """
        Hide the currently visible overlay.

        Returns:
            True if an overlay was hidden, False if no overlay is visible
        """
        if not self._current_overlay:
            return False

        overlay_type = self._current_overlay.overlay_type
        return self.hide_overlay(overlay_type)

    def toggle_overlay(self, overlay_type: OverlayType, **kwargs) -> bool:
        """
        Toggle an overlay (show if hidden, hide if shown).

        Args:
            overlay_type: Type of overlay to toggle
            **kwargs: Overlay-specific display options (used when showing)

        Returns:
            True if action was successful, False otherwise
        """
        if self.is_overlay_visible(overlay_type):
            return self.hide_overlay(overlay_type)
        else:
            return self.show_overlay(overlay_type, **kwargs)

    def is_overlay_visible(self, overlay_type: OverlayType) -> bool:
        """
        Check if a specific overlay is currently visible.

        Args:
            overlay_type: Type of overlay to check

        Returns:
            True if overlay is visible, False otherwise
        """
        if overlay_type not in self._overlays:
            return False

        overlay = self._overlays[overlay_type]
        return self._current_overlay == overlay and overlay.is_visible

    def is_any_overlay_visible(self) -> bool:
        """
        Check if any overlay is currently visible.

        Returns:
            True if any overlay is visible, False otherwise
        """
        return self._current_overlay is not None and self._state.is_visible

    def get_current_overlay_type(self) -> Optional[OverlayType]:
        """
        Get the type of the currently visible overlay.

        Returns:
            OverlayType if an overlay is visible, None otherwise
        """
        return self._state.overlay_type

    def get_element_position(self, number: int) -> Optional[Tuple[int, int]]:
        """
        Get position for a numbered element from the current overlay.

        This method is used by click commands to get the screen position
        for a numbered element.

        Args:
            number: Element number

        Returns:
            Tuple of (x, y) pixel coordinates, or None if not found
        """
        if not self._current_overlay:
            self.logger.warning("No overlay visible for element %d", number)
            return None

        # First try getting from state (most overlays populate this)
        position = self._state.get_position(number)
        if position:
            return position

        # Fall back to overlay's own method
        position = self._current_overlay.get_element_position(number)
        if position:
            return position

        self.logger.warning(
            f"Element {number} not found in current overlay "
            f"({self._current_overlay.overlay_type.name})"
        )
        return None

    def update_element_positions(self, positions: Dict[int, Tuple[int, int]]) -> None:
        """
        Update element positions in the current state.

        Overlays can call this to register their element positions.

        Args:
            positions: Dictionary mapping element numbers to (x, y) positions
        """
        self._state.element_positions.update(positions)
        self.logger.debug("Updated %d element positions", len(positions))

    def set_element_position(self, number: int, x: int, y: int) -> None:
        """
        Set position for a single numbered element.

        Args:
            number: Element number
            x: X coordinate in pixels
            y: Y coordinate in pixels
        """
        self._state.set_position(number, x, y)

    def has_element(self, number: int) -> bool:
        """
        Check if the current overlay has a specific element number.

        Args:
            number: Element number to check

        Returns:
            True if element exists, False otherwise
        """
        return self._state.has_element(number)

    def get_state(self) -> OverlayState:
        """
        Get the current overlay state.

        Returns:
            Current OverlayState object
        """
        return self._state

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata in the current state.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._state.metadata[key] = value

    def get_metadata(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get metadata from the current state.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._state.metadata.get(key, default)

    def clear_all(self) -> None:
        """Clear all overlays and state (useful for cleanup/testing)."""
        # Hide current overlay
        self.hide_current_overlay()

        # Clear all registrations
        self._overlays.clear()
        self._state.clear()

        self.logger.debug("Cleared all overlays")
