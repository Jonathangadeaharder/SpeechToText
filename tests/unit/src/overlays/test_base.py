"""Unit tests for overlay base classes."""

import pytest

from src.overlays.base import Overlay, OverlayState, OverlayType


class TestOverlayState:
    """Test OverlayState dataclass."""

    def test_default_initialization(self):
        """Test default state initialization."""
        state = OverlayState()

        assert state.is_visible is False
        assert state.overlay_type is None
        assert len(state.element_positions) == 0
        assert len(state.metadata) == 0

    def test_custom_initialization(self):
        """Test custom state initialization."""
        state = OverlayState(
            is_visible=True,
            overlay_type=OverlayType.GRID,
            element_positions={1: (100, 200), 2: (300, 400)},
            metadata={"grid_size": 9}
        )

        assert state.is_visible is True
        assert state.overlay_type == OverlayType.GRID
        assert len(state.element_positions) == 2
        assert state.element_positions[1] == (100, 200)
        assert state.metadata["grid_size"] == 9

    def test_clear(self):
        """Test clearing state."""
        state = OverlayState(
            is_visible=True,
            overlay_type=OverlayType.GRID,
            element_positions={1: (100, 200)},
            metadata={"test": "data"}
        )

        state.clear()

        assert state.is_visible is False
        assert state.overlay_type is None
        assert len(state.element_positions) == 0
        assert len(state.metadata) == 0

    def test_get_position(self):
        """Test getting element position."""
        state = OverlayState()
        state.element_positions = {1: (100, 200), 2: (300, 400)}

        assert state.get_position(1) == (100, 200)
        assert state.get_position(2) == (300, 400)
        assert state.get_position(3) is None

    def test_set_position(self):
        """Test setting element position."""
        state = OverlayState()

        state.set_position(1, 100, 200)
        state.set_position(2, 300, 400)

        assert state.element_positions[1] == (100, 200)
        assert state.element_positions[2] == (300, 400)

    def test_has_element(self):
        """Test checking if element exists."""
        state = OverlayState()
        state.element_positions = {1: (100, 200), 5: (300, 400)}

        assert state.has_element(1) is True
        assert state.has_element(5) is True
        assert state.has_element(2) is False
        assert state.has_element(10) is False


class TestOverlayType:
    """Test OverlayType enum."""

    def test_overlay_types_exist(self):
        """Test that all overlay types are defined."""
        assert OverlayType.GRID is not None
        assert OverlayType.ELEMENT is not None
        assert OverlayType.WINDOW is not None
        assert OverlayType.HELP is not None

    def test_overlay_types_unique(self):
        """Test that overlay types are unique."""
        types = [OverlayType.GRID, OverlayType.ELEMENT, OverlayType.WINDOW, OverlayType.HELP]
        assert len(types) == len(set(types))

    def test_overlay_type_names(self):
        """Test overlay type names."""
        assert OverlayType.GRID.name == "GRID"
        assert OverlayType.ELEMENT.name == "ELEMENT"
        assert OverlayType.WINDOW.name == "WINDOW"
        assert OverlayType.HELP.name == "HELP"


class ConcreteOverlay(Overlay):
    """Concrete implementation for testing abstract Overlay."""

    def __init__(self):
        self.visible = False
        self.positions = {}

    def show(self, **kwargs):
        self.visible = True

    def hide(self):
        self.visible = False

    @property
    def is_visible(self):
        return self.visible

    def handle_input(self, text: str):
        return text == "test"

    @property
    def overlay_type(self):
        return OverlayType.GRID

    def get_element_position(self, number: int):
        return self.positions.get(number)


class TestOverlay:
    """Test Overlay abstract base class."""

    def test_concrete_implementation(self):
        """Test that concrete implementation works."""
        overlay = ConcreteOverlay()

        # Test show/hide
        assert overlay.is_visible is False
        overlay.show()
        assert overlay.is_visible is True
        overlay.hide()
        assert overlay.is_visible is False

    def test_handle_input(self):
        """Test input handling."""
        overlay = ConcreteOverlay()

        assert overlay.handle_input("test") is True
        assert overlay.handle_input("other") is False

    def test_overlay_type(self):
        """Test overlay type property."""
        overlay = ConcreteOverlay()
        assert overlay.overlay_type == OverlayType.GRID

    def test_get_element_position(self):
        """Test getting element position."""
        overlay = ConcreteOverlay()
        overlay.positions = {1: (100, 200), 2: (300, 400)}

        assert overlay.get_element_position(1) == (100, 200)
        assert overlay.get_element_position(2) == (300, 400)
        assert overlay.get_element_position(3) is None

    def test_validate_before_show_default(self):
        """Test default validate_before_show."""
        overlay = ConcreteOverlay()
        assert overlay.validate_before_show() is True

    def test_on_show_hook(self):
        """Test on_show hook (should do nothing by default)."""
        overlay = ConcreteOverlay()
        overlay.on_show()  # Should not raise

    def test_on_hide_hook(self):
        """Test on_hide hook (should do nothing by default)."""
        overlay = ConcreteOverlay()
        overlay.on_hide()  # Should not raise

    def test_show_with_kwargs(self):
        """Test show method accepts kwargs."""
        overlay = ConcreteOverlay()
        overlay.show(grid_size=9, test_param="value")  # Should not raise
        assert overlay.is_visible is True

    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented."""
        # Cannot instantiate Overlay directly
        with pytest.raises(TypeError):
            Overlay()


class CustomValidationOverlay(ConcreteOverlay):
    """Overlay with custom validation."""

    def __init__(self, allow_show=True):
        super().__init__()
        self.allow_show = allow_show

    def validate_before_show(self):
        return self.allow_show


class TestOverlayValidation:
    """Test overlay validation."""

    def test_validate_before_show_success(self):
        """Test successful validation."""
        overlay = CustomValidationOverlay(allow_show=True)
        assert overlay.validate_before_show() is True

    def test_validate_before_show_failure(self):
        """Test failed validation."""
        overlay = CustomValidationOverlay(allow_show=False)
        assert overlay.validate_before_show() is False


class OverlayWithHooks(ConcreteOverlay):
    """Overlay with custom hooks."""

    def __init__(self):
        super().__init__()
        self.show_called = False
        self.hide_called = False

    def on_show(self):
        self.show_called = True

    def on_hide(self):
        self.hide_called = True


class TestOverlayHooks:
    """Test overlay lifecycle hooks."""

    def test_on_show_called(self):
        """Test on_show hook is called."""
        overlay = OverlayWithHooks()
        assert overlay.show_called is False

        overlay.show()
        overlay.on_show()

        assert overlay.show_called is True

    def test_on_hide_called(self):
        """Test on_hide hook is called."""
        overlay = OverlayWithHooks()
        assert overlay.hide_called is False

        overlay.hide()
        overlay.on_hide()

        assert overlay.hide_called is True
