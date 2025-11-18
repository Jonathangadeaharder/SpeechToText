"""Unit tests for FeedbackOverlay."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk

from src.overlays.feedback_overlay import FeedbackOverlay
from src.overlays.base import OverlayType


class TestFeedbackOverlayInit:
    """Test FeedbackOverlay initialization."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_init_default(self, mock_start_ui):
        """Test default initialization."""
        overlay = FeedbackOverlay()

        assert overlay.screen_width == 1920
        assert overlay.screen_height == 1080
        assert overlay.duration == 1.5
        assert overlay.position == "top-right"
        assert overlay._visible is False
        assert overlay._window is None
        mock_start_ui.assert_called_once()

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_init_custom_params(self, mock_start_ui):
        """Test initialization with custom parameters."""
        overlay = FeedbackOverlay(
            screen_width=2560,
            screen_height=1440,
            duration=2.0,
            position="top-left"
        )

        assert overlay.screen_width == 2560
        assert overlay.screen_height == 1440
        assert overlay.duration == 2.0
        assert overlay.position == "top-left"


class TestFeedbackOverlayProperties:
    """Test FeedbackOverlay properties."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_overlay_type(self, mock_start_ui):
        """Test overlay type."""
        overlay = FeedbackOverlay()
        assert overlay.overlay_type == OverlayType.FEEDBACK

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_is_visible_false(self, mock_start_ui):
        """Test is_visible when not shown."""
        overlay = FeedbackOverlay()
        assert overlay.is_visible is False

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_is_visible_true(self, mock_start_ui):
        """Test is_visible when shown."""
        overlay = FeedbackOverlay()
        overlay._visible = True
        overlay._window = Mock()
        assert overlay.is_visible is True


class TestFeedbackOverlayShowHide:
    """Test showing and hiding feedback overlay."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_show_queues_command(self, mock_start_ui):
        """Test showing feedback overlay queues command."""
        overlay = FeedbackOverlay()
        overlay._command_queue = Mock()

        overlay.show(text="Test Command")

        overlay._command_queue.put.assert_called_once_with(("show", "Test Command"))

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_show_default_text(self, mock_start_ui):
        """Test showing feedback overlay with default text."""
        overlay = FeedbackOverlay()
        overlay._command_queue = Mock()

        overlay.show()

        overlay._command_queue.put.assert_called_once_with(("show", "Command Executed"))

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_hide_queues_command(self, mock_start_ui):
        """Test hiding feedback overlay queues command."""
        overlay = FeedbackOverlay()
        overlay._command_queue = Mock()

        overlay.hide()

        overlay._command_queue.put.assert_called_once_with(("hide", None))


class TestFeedbackOverlayPosition:
    """Test feedback overlay position calculation."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_calculate_position_top_right(self, mock_start_ui):
        """Test position calculation for top-right."""
        overlay = FeedbackOverlay(position="top-right")
        x, y = overlay._calculate_position(300, 60)

        assert x == 1920 - 300 - 20  # screen_width - width - padding
        assert y == 20  # padding

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_calculate_position_top_left(self, mock_start_ui):
        """Test position calculation for top-left."""
        overlay = FeedbackOverlay(position="top-left")
        x, y = overlay._calculate_position(300, 60)

        assert x == 20  # padding
        assert y == 20  # padding

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_calculate_position_bottom_right(self, mock_start_ui):
        """Test position calculation for bottom-right."""
        overlay = FeedbackOverlay(position="bottom-right")
        x, y = overlay._calculate_position(300, 60)

        assert x == 1920 - 300 - 20  # screen_width - width - padding
        assert y == 1080 - 60 - 20  # screen_height - height - padding

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_calculate_position_center(self, mock_start_ui):
        """Test position calculation for center."""
        overlay = FeedbackOverlay(position="center")
        x, y = overlay._calculate_position(300, 60)

        assert x == (1920 - 300) // 2
        assert y == (1080 - 60) // 2

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_calculate_position_invalid_defaults_to_top_right(self, mock_start_ui):
        """Test position calculation with invalid position defaults to top-right."""
        overlay = FeedbackOverlay(position="invalid")
        x, y = overlay._calculate_position(300, 60)

        assert x == 1920 - 300 - 20
        assert y == 20


class TestFeedbackOverlayValidation:
    """Test feedback overlay validation."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_validate_before_show_valid(self, mock_start_ui):
        """Test validation with valid screen dimensions."""
        overlay = FeedbackOverlay(screen_width=1920, screen_height=1080)
        assert overlay.validate_before_show() is True

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_validate_before_show_invalid_width(self, mock_start_ui):
        """Test validation with invalid screen width."""
        overlay = FeedbackOverlay(screen_width=0, screen_height=1080)
        assert overlay.validate_before_show() is False

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_validate_before_show_invalid_height(self, mock_start_ui):
        """Test validation with invalid screen height."""
        overlay = FeedbackOverlay(screen_width=1920, screen_height=-1)
        assert overlay.validate_before_show() is False


class TestFeedbackOverlayHandleInput:
    """Test feedback overlay input handling."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_handle_input_returns_false(self, mock_start_ui):
        """Test handle_input always returns False."""
        overlay = FeedbackOverlay()
        assert overlay.handle_input("test") is False


class TestFeedbackOverlayGetElementPosition:
    """Test feedback overlay element position."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_get_element_position_returns_none(self, mock_start_ui):
        """Test get_element_position always returns None."""
        overlay = FeedbackOverlay()
        assert overlay.get_element_position(1) is None


class TestFeedbackOverlayCleanup:
    """Test feedback overlay cleanup."""

    @patch('src.overlays.feedback_overlay.FeedbackOverlay._start_ui_thread')
    def test_cleanup(self, mock_start_ui):
        """Test cleanup stops UI thread."""
        overlay = FeedbackOverlay()
        overlay._command_queue = Mock()
        overlay._ui_thread = Mock()
        overlay._ui_thread.is_alive.return_value = True

        overlay.cleanup()

        assert overlay._running is False
        overlay._command_queue.put.assert_called_once_with(("stop", None))
        overlay._ui_thread.join.assert_called_once_with(timeout=2.0)
