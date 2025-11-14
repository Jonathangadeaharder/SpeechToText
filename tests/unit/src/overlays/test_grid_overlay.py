"""Unit tests for GridOverlay."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.overlays.grid_overlay import GridOverlay
from src.overlays.base import OverlayType


class TestGridOverlayInit:
    """Test GridOverlay initialization."""

    def test_init_default(self):
        """Test default initialization."""
        overlay = GridOverlay()

        assert overlay.screen_width == 1920
        assert overlay.screen_height == 1080
        assert overlay._visible is False
        assert overlay._window is None
        assert overlay._grid_size == 9

    def test_init_custom(self):
        """Test custom initialization."""
        overlay = GridOverlay(screen_width=2560, screen_height=1440)

        assert overlay.screen_width == 2560
        assert overlay.screen_height == 1440


class TestGridOverlayProperties:
    """Test GridOverlay properties."""

    def test_overlay_type(self):
        """Test overlay type."""
        overlay = GridOverlay()
        assert overlay.overlay_type == OverlayType.GRID

    def test_is_visible_false(self):
        """Test is_visible when not shown."""
        overlay = GridOverlay()
        assert overlay.is_visible is False

    @patch('tkinter.Tk')
    def test_is_visible_true(self, mock_tk):
        """Test is_visible when shown."""
        overlay = GridOverlay()
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay.show()

        assert overlay.is_visible is True


class TestGridOverlayShowHide:
    """Test showing and hiding grid overlay."""

    @patch('tkinter.Tk')
    def test_show(self, mock_tk):
        """Test showing grid overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = GridOverlay()
        overlay.show(grid_size=9)

        assert overlay._visible is True
        assert overlay._grid_size == 9
        mock_tk.assert_called_once()

    @patch('tkinter.Tk')
    def test_show_different_sizes(self, mock_tk):
        """Test showing grid with different sizes."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = GridOverlay()

        overlay.show(grid_size=3)
        assert overlay._grid_size == 3

        overlay.show(grid_size=5)
        assert overlay._grid_size == 5

        overlay.show(grid_size=9)
        assert overlay._grid_size == 9

    @patch('tkinter.Tk')
    def test_hide(self, mock_tk):
        """Test hiding grid overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = GridOverlay()
        overlay.show()
        overlay.hide()

        assert overlay._visible is False
        assert overlay._window is None
        mock_window.destroy.assert_called_once()

    def test_hide_when_not_shown(self):
        """Test hiding when not shown."""
        overlay = GridOverlay()
        overlay.hide()  # Should not raise

        assert overlay._visible is False


class TestGridOverlayElementPosition:
    """Test getting element positions."""

    def test_get_element_position_valid(self):
        """Test getting valid element position."""
        overlay = GridOverlay(screen_width=900, screen_height=900)
        overlay._grid_size = 3  # 3x3 grid

        # Cell 1 (top-left): should be at center of first cell
        pos = overlay.get_element_position(1)
        assert pos == (150, 150)  # Center of 300x300 cell

        # Cell 5 (center): should be at center
        pos = overlay.get_element_position(5)
        assert pos == (450, 450)

        # Cell 9 (bottom-right): should be at center of last cell
        pos = overlay.get_element_position(9)
        assert pos == (750, 750)

    def test_get_element_position_invalid(self):
        """Test getting invalid element position."""
        overlay = GridOverlay()
        overlay._grid_size = 3

        assert overlay.get_element_position(0) is None
        assert overlay.get_element_position(10) is None
        assert overlay.get_element_position(-1) is None

    def test_get_element_position_9x9_grid(self):
        """Test positions in 9x9 grid."""
        overlay = GridOverlay(screen_width=1800, screen_height=1800)
        overlay._grid_size = 9

        # Cell 1 (top-left corner)
        pos = overlay.get_element_position(1)
        assert pos == (100, 100)  # Center of 200x200 cell

        # Cell 41 (center cell of 9x9)
        pos = overlay.get_element_position(41)
        assert pos == (900, 900)  # Center of grid

        # Cell 81 (bottom-right corner)
        pos = overlay.get_element_position(81)
        assert pos == (1700, 1700)


class TestGridOverlayRefine:
    """Test grid refinement/zooming."""

    def test_refine_grid_valid(self):
        """Test refining to a valid cell."""
        overlay = GridOverlay(screen_width=900, screen_height=900)
        overlay._grid_size = 3

        result = overlay.refine_grid(5)  # Refine to center cell

        assert result is True
        assert overlay._grid_size == 3  # Should be 3x3 after refinement
        assert overlay._refined_cell == 5
        assert overlay._current_bounds is not None

    def test_refine_grid_invalid(self):
        """Test refining to invalid cell."""
        overlay = GridOverlay()
        overlay._grid_size = 3

        assert overlay.refine_grid(0) is False
        assert overlay.refine_grid(10) is False
        assert overlay._refined_cell is None

    def test_refine_grid_bounds(self):
        """Test refinement calculates correct bounds."""
        overlay = GridOverlay(screen_width=900, screen_height=900)
        overlay._grid_size = 3

        # Refine to cell 1 (top-left)
        overlay.refine_grid(1)
        assert overlay._current_bounds == (0, 0, 300, 300)

        # Refine to cell 5 (center)
        overlay._current_bounds = None  # Reset
        overlay._grid_size = 3
        overlay.refine_grid(5)
        assert overlay._current_bounds == (300, 300, 300, 300)

    def test_is_refined(self):
        """Test checking if grid is refined."""
        overlay = GridOverlay()

        assert overlay.is_refined() is False

        overlay._current_bounds = (100, 100, 200, 200)
        assert overlay.is_refined() is True

    def test_get_refined_cell(self):
        """Test getting refined cell number."""
        overlay = GridOverlay()

        assert overlay.get_refined_cell() is None

        overlay._refined_cell = 5
        assert overlay.get_refined_cell() == 5


class TestGridOverlayValidation:
    """Test validation."""

    def test_validate_before_show_valid(self):
        """Test validation with valid dimensions."""
        overlay = GridOverlay(screen_width=1920, screen_height=1080)

        assert overlay.validate_before_show() is True

    def test_validate_before_show_invalid(self):
        """Test validation with invalid dimensions."""
        overlay = GridOverlay(screen_width=0, screen_height=0)

        assert overlay.validate_before_show() is False

        overlay = GridOverlay(screen_width=-100, screen_height=1080)
        assert overlay.validate_before_show() is False


class TestGridOverlayHelpers:
    """Test helper methods."""

    def test_get_current_grid_size(self):
        """Test getting current grid size."""
        overlay = GridOverlay()

        assert overlay.get_current_grid_size() == 9  # Default

        overlay._grid_size = 5
        assert overlay.get_current_grid_size() == 5

    def test_handle_input(self):
        """Test input handling (should return False)."""
        overlay = GridOverlay()

        assert overlay.handle_input("test") is False
        assert overlay.handle_input("click 5") is False
