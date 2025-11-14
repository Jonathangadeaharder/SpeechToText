"""Unit tests for ElementOverlay."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.overlays.element_overlay import ElementOverlay
from src.overlays.base import OverlayType


class TestElementOverlayInit:
    """Test ElementOverlay initialization."""

    def test_init_default(self):
        """Test default initialization."""
        overlay = ElementOverlay()

        assert overlay.screen_width == 1920
        assert overlay.screen_height == 1080
        assert overlay._visible is False
        assert overlay._window is None
        assert len(overlay._elements) == 0

    @patch('platform.system', return_value='Windows')
    @patch('src.overlays.element_overlay.ElementOverlay._check_ui_automation_available', return_value=True)
    def test_init_windows_with_automation(self, mock_check, mock_platform):
        """Test initialization on Windows with UI Automation."""
        overlay = ElementOverlay()

        assert overlay._use_ui_automation is True

    @patch('platform.system', return_value='Linux')
    def test_init_non_windows(self, mock_platform):
        """Test initialization on non-Windows platform."""
        overlay = ElementOverlay()

        assert overlay._use_ui_automation is False


class TestElementOverlayProperties:
    """Test ElementOverlay properties."""

    def test_overlay_type(self):
        """Test overlay type."""
        overlay = ElementOverlay()
        assert overlay.overlay_type == OverlayType.ELEMENT

    def test_is_visible_false(self):
        """Test is_visible when not shown."""
        overlay = ElementOverlay()
        assert overlay.is_visible is False


class TestElementOverlayShowHide:
    """Test showing and hiding element overlay."""

    @patch('tkinter.Tk')
    @patch.object(ElementOverlay, '_detect_ui_elements', return_value=False)
    @patch.object(ElementOverlay, '_use_fallback_grid')
    def test_show_fallback(self, mock_fallback, mock_detect, mock_tk):
        """Test showing with fallback grid."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = ElementOverlay()
        overlay._use_ui_automation = True
        overlay.show()

        mock_detect.assert_called_once()
        mock_fallback.assert_called_once()
        assert overlay._visible is True

    @patch('tkinter.Tk')
    @patch.object(ElementOverlay, '_use_fallback_grid')
    def test_show_without_automation(self, mock_fallback, mock_tk):
        """Test showing without UI Automation."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = ElementOverlay()
        overlay._use_ui_automation = False
        overlay.show()

        mock_fallback.assert_called_once()
        assert overlay._visible is True

    @patch('tkinter.Tk')
    def test_hide(self, mock_tk):
        """Test hiding element overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = ElementOverlay()
        overlay._use_fallback_grid()
        overlay._create_window()
        overlay._visible = True

        overlay.hide()

        assert overlay._visible is False
        assert overlay._window is None
        assert len(overlay._elements) == 0


class TestElementOverlayFallbackGrid:
    """Test fallback grid functionality."""

    def test_use_fallback_grid(self):
        """Test using fallback 5x5 grid."""
        overlay = ElementOverlay(screen_width=1000, screen_height=1000)
        overlay._use_fallback_grid()

        assert len(overlay._elements) == 25  # 5x5 grid

        # Check first element (top-left)
        assert overlay._elements[0] == (0, 0, 200, 200)

        # Check last element (bottom-right)
        assert overlay._elements[24] == (800, 800, 200, 200)

    def test_fallback_grid_different_screen_size(self):
        """Test fallback grid with different screen size."""
        overlay = ElementOverlay(screen_width=2000, screen_height=1000)
        overlay._use_fallback_grid()

        assert len(overlay._elements) == 25
        # Cell width should be 400, height should be 200
        assert overlay._elements[0] == (0, 0, 400, 200)


class TestElementOverlayElementPosition:
    """Test getting element positions."""

    def test_get_element_position_valid(self):
        """Test getting valid element position."""
        overlay = ElementOverlay()
        overlay._elements = [
            (100, 200, 50, 60),  # Element 1
            (300, 400, 70, 80),  # Element 2
        ]

        # Element 1: center at (100 + 50/2, 200 + 60/2) = (125, 230)
        pos = overlay.get_element_position(1)
        assert pos == (125, 230)

        # Element 2: center at (300 + 70/2, 400 + 80/2) = (335, 440)
        pos = overlay.get_element_position(2)
        assert pos == (335, 440)

    def test_get_element_position_invalid(self):
        """Test getting invalid element position."""
        overlay = ElementOverlay()
        overlay._elements = [(100, 200, 50, 60)]

        assert overlay.get_element_position(0) is None
        assert overlay.get_element_position(2) is None
        assert overlay.get_element_position(-1) is None


class TestElementOverlayValidation:
    """Test validation."""

    def test_validate_before_show_valid(self):
        """Test validation with valid dimensions."""
        overlay = ElementOverlay(screen_width=1920, screen_height=1080)

        assert overlay.validate_before_show() is True

    def test_validate_before_show_invalid(self):
        """Test validation with invalid dimensions."""
        overlay = ElementOverlay(screen_width=0, screen_height=0)

        assert overlay.validate_before_show() is False


class TestElementOverlayHelpers:
    """Test helper methods."""

    def test_get_element_count(self):
        """Test getting element count."""
        overlay = ElementOverlay()

        assert overlay.get_element_count() == 0

        overlay._elements = [(100, 200, 50, 60), (300, 400, 70, 80)]
        assert overlay.get_element_count() == 2

    def test_is_using_ui_automation(self):
        """Test checking if using UI Automation."""
        overlay = ElementOverlay()
        overlay._use_ui_automation = False

        assert overlay.is_using_ui_automation() is False

        overlay._use_ui_automation = True
        overlay._elements = [(100, 200, 50, 60)]
        assert overlay.is_using_ui_automation() is True

    def test_handle_input(self):
        """Test input handling (should return False)."""
        overlay = ElementOverlay()

        assert overlay.handle_input("test") is False
