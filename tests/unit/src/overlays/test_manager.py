"""Unit tests for OverlayManager."""

import pytest
from unittest.mock import Mock, MagicMock

from src.core.events import EventBus, EventType
from src.overlays.base import Overlay, OverlayType
from src.overlays.manager import OverlayManager


class MockOverlay(Overlay):
    """Mock overlay for testing."""

    def __init__(self, overlay_type=OverlayType.GRID):
        self._visible = False
        self._type = overlay_type
        self._validate_result = True
        self.show_called = False
        self.hide_called = False
        self.on_show_called = False
        self.on_hide_called = False
        self.show_kwargs = None

    def show(self, **kwargs):
        self.show_called = True
        self.show_kwargs = kwargs
        self._visible = True

    def hide(self):
        self.hide_called = True
        self._visible = False

    @property
    def is_visible(self):
        return self._visible

    def handle_input(self, text: str):
        return False

    @property
    def overlay_type(self):
        return self._type

    def validate_before_show(self):
        return self._validate_result

    def on_show(self):
        self.on_show_called = True

    def on_hide(self):
        self.on_hide_called = True


class TestOverlayManagerInit:
    """Test OverlayManager initialization."""

    def test_init_without_event_bus(self):
        """Test initialization without event bus."""
        manager = OverlayManager()

        assert manager.event_bus is None
        assert len(manager._overlays) == 0
        assert manager._current_overlay is None
        assert manager._state.is_visible is False

    def test_init_with_event_bus(self):
        """Test initialization with event bus."""
        event_bus = EventBus()
        manager = OverlayManager(event_bus)

        assert manager.event_bus == event_bus


class TestOverlayManagerRegistration:
    """Test overlay registration."""

    def test_register_overlay(self):
        """Test registering an overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)

        assert OverlayType.GRID in manager._overlays
        assert manager._overlays[OverlayType.GRID] == overlay

    def test_register_multiple_overlays(self):
        """Test registering multiple overlays."""
        manager = OverlayManager()
        grid_overlay = MockOverlay(OverlayType.GRID)
        element_overlay = MockOverlay(OverlayType.ELEMENT)

        manager.register_overlay(OverlayType.GRID, grid_overlay)
        manager.register_overlay(OverlayType.ELEMENT, element_overlay)

        assert len(manager._overlays) == 2
        assert manager._overlays[OverlayType.GRID] == grid_overlay
        assert manager._overlays[OverlayType.ELEMENT] == element_overlay

    def test_unregister_overlay(self):
        """Test unregistering an overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        result = manager.unregister_overlay(OverlayType.GRID)

        assert result is True
        assert OverlayType.GRID not in manager._overlays

    def test_unregister_nonexistent_overlay(self):
        """Test unregistering overlay that doesn't exist."""
        manager = OverlayManager()

        result = manager.unregister_overlay(OverlayType.GRID)

        assert result is False

    def test_unregister_visible_overlay(self):
        """Test unregistering overlay that is currently visible."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        assert overlay.is_visible is True

        result = manager.unregister_overlay(OverlayType.GRID)

        assert result is True
        assert overlay.is_visible is False
        assert overlay.hide_called is True


class TestOverlayManagerShow:
    """Test showing overlays."""

    def test_show_overlay(self):
        """Test showing an overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        result = manager.show_overlay(OverlayType.GRID)

        assert result is True
        assert overlay.show_called is True
        assert overlay.on_show_called is True
        assert overlay.is_visible is True
        assert manager._current_overlay == overlay
        assert manager._state.is_visible is True
        assert manager._state.overlay_type == OverlayType.GRID

    def test_show_overlay_with_kwargs(self):
        """Test showing overlay with keyword arguments."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        result = manager.show_overlay(OverlayType.GRID, grid_size=9, test="value")

        assert result is True
        assert overlay.show_kwargs == {"grid_size": 9, "test": "value"}

    def test_show_unregistered_overlay(self):
        """Test showing overlay that isn't registered."""
        manager = OverlayManager()

        result = manager.show_overlay(OverlayType.GRID)

        assert result is False

    def test_show_overlay_validation_failure(self):
        """Test showing overlay when validation fails."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)
        overlay._validate_result = False

        manager.register_overlay(OverlayType.GRID, overlay)
        result = manager.show_overlay(OverlayType.GRID)

        assert result is False
        assert overlay.show_called is False

    def test_show_overlay_hides_current(self):
        """Test showing overlay hides currently visible overlay."""
        manager = OverlayManager()
        overlay1 = MockOverlay(OverlayType.GRID)
        overlay2 = MockOverlay(OverlayType.ELEMENT)

        manager.register_overlay(OverlayType.GRID, overlay1)
        manager.register_overlay(OverlayType.ELEMENT, overlay2)

        manager.show_overlay(OverlayType.GRID)
        assert overlay1.is_visible is True

        manager.show_overlay(OverlayType.ELEMENT)

        assert overlay1.is_visible is False
        assert overlay1.hide_called is True
        assert overlay2.is_visible is True
        assert manager._current_overlay == overlay2

    def test_show_same_overlay_twice(self):
        """Test showing same overlay when already visible."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)

        manager.show_overlay(OverlayType.GRID)
        overlay.show_called = False  # Reset

        manager.show_overlay(OverlayType.GRID)

        assert overlay.show_called is True  # Should still call show

    def test_show_overlay_publishes_event(self):
        """Test showing overlay publishes event."""
        event_bus = EventBus()
        manager = OverlayManager(event_bus)
        overlay = MockOverlay(OverlayType.GRID)

        events = []
        event_bus.subscribe(EventType.OVERLAY_SHOWN, lambda e: events.append(e))

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID, grid_size=9)

        assert len(events) == 1
        assert events[0].event_type == EventType.OVERLAY_SHOWN
        assert events[0].data["overlay_type"] == "GRID"
        assert events[0].data["kwargs"] == {"grid_size": 9}


class TestOverlayManagerHide:
    """Test hiding overlays."""

    def test_hide_overlay(self):
        """Test hiding an overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        result = manager.hide_overlay(OverlayType.GRID)

        assert result is True
        assert overlay.hide_called is True
        assert overlay.on_hide_called is True
        assert overlay.is_visible is False
        assert manager._current_overlay is None
        assert manager._state.is_visible is False
        assert manager._state.overlay_type is None

    def test_hide_unregistered_overlay(self):
        """Test hiding overlay that isn't registered."""
        manager = OverlayManager()

        result = manager.hide_overlay(OverlayType.GRID)

        assert result is False

    def test_hide_overlay_not_visible(self):
        """Test hiding overlay that isn't currently visible."""
        manager = OverlayManager()
        overlay1 = MockOverlay(OverlayType.GRID)
        overlay2 = MockOverlay(OverlayType.ELEMENT)

        manager.register_overlay(OverlayType.GRID, overlay1)
        manager.register_overlay(OverlayType.ELEMENT, overlay2)

        manager.show_overlay(OverlayType.GRID)

        result = manager.hide_overlay(OverlayType.ELEMENT)

        assert result is False
        assert overlay2.hide_called is False

    def test_hide_current_overlay(self):
        """Test hiding current overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        result = manager.hide_current_overlay()

        assert result is True
        assert overlay.hide_called is True
        assert manager._current_overlay is None

    def test_hide_current_overlay_when_none_visible(self):
        """Test hiding current overlay when none is visible."""
        manager = OverlayManager()

        result = manager.hide_current_overlay()

        assert result is False

    def test_hide_overlay_publishes_event(self):
        """Test hiding overlay publishes event."""
        event_bus = EventBus()
        manager = OverlayManager(event_bus)
        overlay = MockOverlay(OverlayType.GRID)

        events = []
        event_bus.subscribe(EventType.OVERLAY_HIDDEN, lambda e: events.append(e))

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)
        manager.hide_overlay(OverlayType.GRID)

        assert len(events) == 1
        assert events[0].event_type == EventType.OVERLAY_HIDDEN
        assert events[0].data["overlay_type"] == "GRID"


class TestOverlayManagerToggle:
    """Test toggling overlays."""

    def test_toggle_hidden_overlay(self):
        """Test toggling shows hidden overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        result = manager.toggle_overlay(OverlayType.GRID)

        assert result is True
        assert overlay.is_visible is True

    def test_toggle_visible_overlay(self):
        """Test toggling hides visible overlay."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        result = manager.toggle_overlay(OverlayType.GRID)

        assert result is True
        assert overlay.is_visible is False


class TestOverlayManagerVisibility:
    """Test visibility checks."""

    def test_is_overlay_visible_true(self):
        """Test checking if specific overlay is visible."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        assert manager.is_overlay_visible(OverlayType.GRID) is True

    def test_is_overlay_visible_false(self):
        """Test checking if overlay is not visible."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)

        assert manager.is_overlay_visible(OverlayType.GRID) is False

    def test_is_overlay_visible_unregistered(self):
        """Test checking visibility of unregistered overlay."""
        manager = OverlayManager()

        assert manager.is_overlay_visible(OverlayType.GRID) is False

    def test_is_any_overlay_visible_true(self):
        """Test checking if any overlay is visible."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        assert manager.is_any_overlay_visible() is True

    def test_is_any_overlay_visible_false(self):
        """Test checking when no overlay is visible."""
        manager = OverlayManager()

        assert manager.is_any_overlay_visible() is False

    def test_get_current_overlay_type(self):
        """Test getting current overlay type."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        assert manager.get_current_overlay_type() == OverlayType.GRID

    def test_get_current_overlay_type_none(self):
        """Test getting current overlay type when none visible."""
        manager = OverlayManager()

        assert manager.get_current_overlay_type() is None


class TestOverlayManagerElementPositions:
    """Test element position management."""

    def test_get_element_position(self):
        """Test getting element position."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)
        manager.set_element_position(1, 100, 200)

        position = manager.get_element_position(1)

        assert position == (100, 200)

    def test_get_element_position_no_overlay(self):
        """Test getting element position with no overlay visible."""
        manager = OverlayManager()

        position = manager.get_element_position(1)

        assert position is None

    def test_update_element_positions(self):
        """Test updating multiple element positions."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        positions = {1: (100, 200), 2: (300, 400), 3: (500, 600)}
        manager.update_element_positions(positions)

        assert manager.get_element_position(1) == (100, 200)
        assert manager.get_element_position(2) == (300, 400)
        assert manager.get_element_position(3) == (500, 600)

    def test_has_element(self):
        """Test checking if element exists."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)
        manager.set_element_position(1, 100, 200)

        assert manager.has_element(1) is True
        assert manager.has_element(2) is False


class TestOverlayManagerMetadata:
    """Test metadata management."""

    def test_set_metadata(self):
        """Test setting metadata."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        manager.set_metadata("grid_size", 9)
        manager.set_metadata("test", "value")

        assert manager._state.metadata["grid_size"] == 9
        assert manager._state.metadata["test"] == "value"

    def test_get_metadata(self):
        """Test getting metadata."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)
        manager.set_metadata("grid_size", 9)

        assert manager.get_metadata("grid_size") == 9
        assert manager.get_metadata("nonexistent") is None
        assert manager.get_metadata("nonexistent", "default") == "default"


class TestOverlayManagerState:
    """Test state management."""

    def test_get_state(self):
        """Test getting state object."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)

        state = manager.get_state()

        assert state.is_visible is True
        assert state.overlay_type == OverlayType.GRID

    def test_clear_all(self):
        """Test clearing all overlays and state."""
        manager = OverlayManager()
        overlay = MockOverlay(OverlayType.GRID)

        manager.register_overlay(OverlayType.GRID, overlay)
        manager.show_overlay(OverlayType.GRID)
        manager.set_element_position(1, 100, 200)

        manager.clear_all()

        assert len(manager._overlays) == 0
        assert manager._current_overlay is None
        assert manager._state.is_visible is False
        assert len(manager._state.element_positions) == 0
