"""Unit tests for WindowListOverlay."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.overlays.window_overlay import WindowListOverlay
from src.overlays.base import OverlayType


class TestWindowListOverlayInit:
    """Test WindowListOverlay initialization."""

    def test_init_default(self):
        """Test default initialization."""
        overlay = WindowListOverlay()

        assert overlay.screen_width == 1920
        assert overlay.screen_height == 1080
        assert overlay._visible is False
        assert overlay._window is None
        assert len(overlay._windows) == 0


class TestWindowListOverlayProperties:
    """Test WindowListOverlay properties."""

    def test_overlay_type(self):
        """Test overlay type."""
        overlay = WindowListOverlay()
        assert overlay.overlay_type == OverlayType.WINDOW

    def test_is_visible_false(self):
        """Test is_visible when not shown."""
        overlay = WindowListOverlay()
        assert overlay.is_visible is False


class TestWindowListOverlayShowHide:
    """Test showing and hiding window list overlay."""

    @patch('tkinter.Tk')
    @patch.object(WindowListOverlay, '_enumerate_windows')
    def test_show(self, mock_enumerate, mock_tk):
        """Test showing window list overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = WindowListOverlay()
        overlay.show()

        mock_enumerate.assert_called_once_with(20)
        assert overlay._visible is True

    @patch('tkinter.Tk')
    def test_hide(self, mock_tk):
        """Test hiding window list overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = WindowListOverlay()
        overlay._windows = [{"title": "Test"}]
        overlay._window = mock_window
        overlay._visible = True

        overlay.hide()

        assert overlay._visible is False
        assert overlay._window is None
        assert len(overlay._windows) == 0


class TestWindowListOverlayEnumeration:
    """Test window enumeration."""

    @patch('platform.system', return_value='Windows')
    @patch.object(WindowListOverlay, '_enumerate_windows_windows')
    def test_enumerate_windows_windows(self, mock_enum_win, mock_platform):
        """Test enumerating windows on Windows."""
        mock_enum_win.return_value = [{"hwnd": 123, "title": "Test"}]

        overlay = WindowListOverlay()
        overlay._enumerate_windows(10)

        mock_enum_win.assert_called_once_with(10)

    @patch('platform.system', return_value='Linux')
    @patch.object(WindowListOverlay, '_enumerate_windows_linux')
    def test_enumerate_windows_linux(self, mock_enum_linux, mock_platform):
        """Test enumerating windows on Linux."""
        mock_enum_linux.return_value = [{"id": "0x123", "title": "Test"}]

        overlay = WindowListOverlay()
        overlay._enumerate_windows(10)

        mock_enum_linux.assert_called_once_with(10)

    @patch('platform.system', return_value='Darwin')
    @patch.object(WindowListOverlay, '_enumerate_windows_macos')
    def test_enumerate_windows_macos(self, mock_enum_mac, mock_platform):
        """Test enumerating windows on macOS."""
        mock_enum_mac.return_value = []

        overlay = WindowListOverlay()
        overlay._enumerate_windows(10)

        mock_enum_mac.assert_called_once_with(10)


class TestWindowListOverlayElementPosition:
    """Test getting element positions."""

    def test_get_element_position_valid(self):
        """Test getting valid element position."""
        overlay = WindowListOverlay(screen_width=1920, screen_height=1080)
        overlay._windows = [
            {"title": "Window 1"},
            {"title": "Window 2"},
            {"title": "Window 3"},
        ]

        # Window 1 should be at y=100+0*40+20 = 120
        pos = overlay.get_element_position(1)
        assert pos == (960, 120)

        # Window 2 should be at y=100+1*40+20 = 160
        pos = overlay.get_element_position(2)
        assert pos == (960, 160)

    def test_get_element_position_invalid(self):
        """Test getting invalid element position."""
        overlay = WindowListOverlay()
        overlay._windows = [{"title": "Window 1"}]

        assert overlay.get_element_position(0) is None
        assert overlay.get_element_position(2) is None


class TestWindowListOverlayWindowInfo:
    """Test getting window information."""

    def test_get_window_info_valid(self):
        """Test getting valid window info."""
        overlay = WindowListOverlay()
        overlay._windows = [
            {"hwnd": 123, "title": "Test 1"},
            {"hwnd": 456, "title": "Test 2"},
        ]

        info = overlay.get_window_info(1)
        assert info == {"hwnd": 123, "title": "Test 1"}

        info = overlay.get_window_info(2)
        assert info == {"hwnd": 456, "title": "Test 2"}

    def test_get_window_info_invalid(self):
        """Test getting invalid window info."""
        overlay = WindowListOverlay()
        overlay._windows = [{"title": "Test"}]

        assert overlay.get_window_info(0) is None
        assert overlay.get_window_info(2) is None


class TestWindowListOverlaySwitching:
    """Test window switching."""

    @patch('platform.system', return_value='Windows')
    @patch.object(WindowListOverlay, '_switch_to_window_windows')
    def test_switch_to_window_windows(self, mock_switch, mock_platform):
        """Test switching to window on Windows."""
        mock_switch.return_value = True

        overlay = WindowListOverlay()
        overlay._windows = [{"hwnd": 123, "title": "Test"}]

        result = overlay.switch_to_window(1)

        assert result is True
        mock_switch.assert_called_once()

    @patch('platform.system', return_value='Linux')
    @patch.object(WindowListOverlay, '_switch_to_window_linux')
    def test_switch_to_window_linux(self, mock_switch, mock_platform):
        """Test switching to window on Linux."""
        mock_switch.return_value = True

        overlay = WindowListOverlay()
        overlay._windows = [{"id": "0x123", "title": "Test"}]

        result = overlay.switch_to_window(1)

        assert result is True
        mock_switch.assert_called_once()

    def test_switch_to_window_invalid(self):
        """Test switching to invalid window."""
        overlay = WindowListOverlay()
        overlay._windows = [{"title": "Test"}]

        result = overlay.switch_to_window(0)
        assert result is False

        result = overlay.switch_to_window(2)
        assert result is False


class TestWindowListOverlayValidation:
    """Test validation."""

    def test_validate_before_show_valid(self):
        """Test validation with valid dimensions."""
        overlay = WindowListOverlay(screen_width=1920, screen_height=1080)

        assert overlay.validate_before_show() is True

    def test_validate_before_show_invalid(self):
        """Test validation with invalid dimensions."""
        overlay = WindowListOverlay(screen_width=0, screen_height=0)

        assert overlay.validate_before_show() is False


class TestWindowListOverlayHelpers:
    """Test helper methods."""

    def test_get_window_count(self):
        """Test getting window count."""
        overlay = WindowListOverlay()

        assert overlay.get_window_count() == 0

        overlay._windows = [{"title": "Test 1"}, {"title": "Test 2"}]
        assert overlay.get_window_count() == 2

    def test_handle_input(self):
        """Test input handling (should return False)."""
        overlay = WindowListOverlay()

        assert overlay.handle_input("test") is False
