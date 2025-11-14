"""Unit tests for HelpOverlay."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.overlays.help_overlay import HelpOverlay
from src.overlays.base import OverlayType


class TestHelpOverlayInit:
    """Test HelpOverlay initialization."""

    def test_init_default(self):
        """Test default initialization."""
        overlay = HelpOverlay()

        assert overlay.screen_width == 1920
        assert overlay.screen_height == 1080
        assert overlay._visible is False
        assert overlay._window is None
        assert overlay.command_registry is None

    def test_init_with_registry(self):
        """Test initialization with command registry."""
        mock_registry = Mock()
        overlay = HelpOverlay(command_registry=mock_registry)

        assert overlay.command_registry == mock_registry


class TestHelpOverlayProperties:
    """Test HelpOverlay properties."""

    def test_overlay_type(self):
        """Test overlay type."""
        overlay = HelpOverlay()
        assert overlay.overlay_type == OverlayType.HELP

    def test_is_visible_false(self):
        """Test is_visible when not shown."""
        overlay = HelpOverlay()
        assert overlay.is_visible is False


class TestHelpOverlayShowHide:
    """Test showing and hiding help overlay."""

    @patch('tkinter.Tk')
    @patch.object(HelpOverlay, '_get_help_text', return_value="Test help text")
    def test_show(self, mock_get_help, mock_tk):
        """Test showing help overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = HelpOverlay()
        overlay.show()

        mock_get_help.assert_called_once()
        assert overlay._visible is True

    @patch('tkinter.Tk')
    def test_hide(self, mock_tk):
        """Test hiding help overlay."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = HelpOverlay()
        overlay._window = mock_window
        overlay._visible = True

        overlay.hide()

        assert overlay._visible is False
        assert overlay._window is None
        mock_window.destroy.assert_called_once()


class TestHelpOverlayHelpText:
    """Test getting help text."""

    def test_get_help_text_from_registry(self):
        """Test getting help text from command registry."""
        mock_registry = Mock()
        mock_registry.get_help_text.return_value = "Registry help text"

        overlay = HelpOverlay(command_registry=mock_registry)
        help_text = overlay._get_help_text()

        assert help_text == "Registry help text"
        mock_registry.get_help_text.assert_called_once_with(enabled_only=True)

    def test_get_help_text_without_registry(self):
        """Test getting help text without registry."""
        overlay = HelpOverlay()
        help_text = overlay._get_help_text()

        assert help_text is not None
        assert "MOUSE CONTROL" in help_text or "Available Commands" in help_text

    def test_get_help_text_registry_error(self):
        """Test getting help text when registry raises error."""
        mock_registry = Mock()
        mock_registry.get_help_text.side_effect = Exception("Test error")

        overlay = HelpOverlay(command_registry=mock_registry)
        help_text = overlay._get_help_text()

        # Should fall back to default help text
        assert help_text is not None

    def test_get_default_help_text(self):
        """Test getting default help text."""
        overlay = HelpOverlay()
        help_text = overlay._get_default_help_text()

        assert "Available Commands" in help_text
        assert "MOUSE CONTROL" in help_text
        assert "SCREEN OVERLAYS" in help_text


class TestHelpOverlayInputHandling:
    """Test input handling."""

    @patch('tkinter.Tk')
    def test_handle_input_close_help(self, mock_tk):
        """Test handling close help command."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = HelpOverlay()
        overlay._window = mock_window
        overlay._visible = True

        result = overlay.handle_input("close help")

        assert result is True
        assert overlay._visible is False

    @patch('tkinter.Tk')
    def test_handle_input_hide_help(self, mock_tk):
        """Test handling hide help command."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = HelpOverlay()
        overlay._window = mock_window
        overlay._visible = True

        result = overlay.handle_input("hide help")

        assert result is True
        assert overlay._visible is False

    @patch('tkinter.Tk')
    def test_handle_input_exit_help(self, mock_tk):
        """Test handling exit help command."""
        mock_window = MagicMock()
        mock_tk.return_value = mock_window

        overlay = HelpOverlay()
        overlay._window = mock_window
        overlay._visible = True

        result = overlay.handle_input("exit help")

        assert result is True
        assert overlay._visible is False

    def test_handle_input_other(self):
        """Test handling other input."""
        overlay = HelpOverlay()

        result = overlay.handle_input("test")
        assert result is False

        result = overlay.handle_input("show grid")
        assert result is False


class TestHelpOverlayParsing:
    """Test help text parsing."""

    def test_parse_help_text_with_sections(self):
        """Test parsing help text with sections."""
        overlay = HelpOverlay()
        help_text = """SECTION 1:
Content for section 1

SECTION 2:
Content for section 2"""

        sections = overlay._parse_help_text(help_text)

        assert len(sections) == 2
        assert sections[0][0] == "SECTION 1:"
        assert "Content for section 1" in sections[0][1]
        assert sections[1][0] == "SECTION 2:"
        assert "Content for section 2" in sections[1][1]

    def test_parse_help_text_without_sections(self):
        """Test parsing help text without sections."""
        overlay = HelpOverlay()
        help_text = """Just some content
without sections"""

        sections = overlay._parse_help_text(help_text)

        assert len(sections) == 1
        assert sections[0][0] == ""
        assert "Just some content" in sections[0][1]


class TestHelpOverlayElementPosition:
    """Test getting element positions."""

    def test_get_element_position(self):
        """Test getting element position (should return None)."""
        overlay = HelpOverlay()

        assert overlay.get_element_position(1) is None
        assert overlay.get_element_position(5) is None


class TestHelpOverlayValidation:
    """Test validation."""

    def test_validate_before_show_valid(self):
        """Test validation with valid dimensions."""
        overlay = HelpOverlay(screen_width=1920, screen_height=1080)

        assert overlay.validate_before_show() is True

    def test_validate_before_show_invalid(self):
        """Test validation with invalid dimensions."""
        overlay = HelpOverlay(screen_width=0, screen_height=0)

        assert overlay.validate_before_show() is False


class TestHelpOverlayHelpers:
    """Test helper methods."""

    def test_set_command_registry(self):
        """Test setting command registry."""
        overlay = HelpOverlay()
        mock_registry = Mock()

        assert overlay.command_registry is None

        overlay.set_command_registry(mock_registry)

        assert overlay.command_registry == mock_registry
