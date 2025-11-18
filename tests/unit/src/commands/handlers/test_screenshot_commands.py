"""Unit tests for screenshot command implementations."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.commands.handlers.screenshot_commands import (
    ScreenshotCommand,
    ReferenceScreenshotCommand
)
from src.commands.base import PRIORITY_MEDIUM
from tests.unit.test_utils import BaseCommandTest


class TestScreenshotCommandInit(unittest.TestCase):
    """Test ScreenshotCommand initialization."""

    @patch('pathlib.Path.mkdir')
    def test_init(self, mock_mkdir):
        """Test screenshot command initialization."""
        cmd = ScreenshotCommand()

        assert cmd.screenshots_dir is not None
        assert "Screenshots" in str(cmd.screenshots_dir)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestScreenshotCommandMatches(unittest.TestCase):
    """Test ScreenshotCommand matching."""

    @patch('pathlib.Path.mkdir')
    def test_matches_screenshot(self, mock_mkdir):
        """Test matching screenshot variations."""
        cmd = ScreenshotCommand()

        assert cmd.matches("screenshot") is True
        assert cmd.matches("SCREENSHOT") is True
        assert cmd.matches("take screenshot") is True
        assert cmd.matches("screen shot") is True
        assert cmd.matches("green shot") is True
        assert cmd.matches("greenshot") is True

    @patch('pathlib.Path.mkdir')
    def test_matches_no_match(self, mock_mkdir):
        """Test no match."""
        cmd = ScreenshotCommand()

        assert cmd.matches("screen") is False
        assert cmd.matches("shot") is False
        assert cmd.matches("reference screenshot") is False


class TestScreenshotCommandExecute(BaseCommandTest):
    """Test ScreenshotCommand execution."""

    @patch('pathlib.Path.mkdir')
    @patch('pyautogui.screenshot')
    def test_execute_screenshot(self, mock_screenshot, mock_mkdir):
        """Test taking a screenshot."""
        mock_image = Mock()
        mock_screenshot.return_value = mock_image

        cmd = ScreenshotCommand()
        result = cmd.execute(self.context, "screenshot")

        assert result is None
        mock_screenshot.assert_called_once()
        mock_image.save.assert_called_once()

    @patch('pathlib.Path.mkdir')
    @patch('pyautogui.screenshot', side_effect=Exception("Screenshot failed"))
    def test_execute_screenshot_error(self, mock_screenshot, mock_mkdir):
        """Test screenshot error handling."""
        cmd = ScreenshotCommand()
        result = cmd.execute(self.context, "screenshot")

        assert result is None


class TestScreenshotCommandProperties(unittest.TestCase):
    """Test ScreenshotCommand properties."""

    @patch('pathlib.Path.mkdir')
    def test_priority(self, mock_mkdir):
        """Test screenshot command priority."""
        cmd = ScreenshotCommand()
        assert cmd.priority == PRIORITY_MEDIUM

    @patch('pathlib.Path.mkdir')
    def test_description(self, mock_mkdir):
        """Test screenshot command description."""
        cmd = ScreenshotCommand()
        assert "screenshot" in cmd.description.lower()

    @patch('pathlib.Path.mkdir')
    def test_examples(self, mock_mkdir):
        """Test screenshot command examples."""
        cmd = ScreenshotCommand()
        assert len(cmd.examples) > 0
        assert "screenshot" in cmd.examples


class TestReferenceScreenshotCommandInit(unittest.TestCase):
    """Test ReferenceScreenshotCommand initialization."""

    def test_init(self):
        """Test reference screenshot command initialization."""
        cmd = ReferenceScreenshotCommand()

        assert cmd.screenshots_dir is not None
        assert "Screenshots" in str(cmd.screenshots_dir)
        assert cmd.single_pattern is not None
        assert cmd.multi_pattern is not None


class TestReferenceScreenshotCommandMatches(unittest.TestCase):
    """Test ReferenceScreenshotCommand matching."""

    def test_matches_reference_screenshot(self):
        """Test matching reference screenshot variations."""
        cmd = ReferenceScreenshotCommand()

        assert cmd.matches("reference screenshot") is True
        assert cmd.matches("reference screenshot 2") is True
        assert cmd.matches("screenshot 1") is True
        assert cmd.matches("latest screenshot") is True
        assert cmd.matches("paste screenshot") is True

    def test_matches_multi_screenshot(self):
        """Test matching multi-screenshot request."""
        cmd = ReferenceScreenshotCommand()

        assert cmd.matches("reference screenshot last 3") is True
        assert cmd.matches("screenshot last 5") is True
        assert cmd.matches("latest screenshot last 10") is True

    def test_matches_no_match(self):
        """Test no match."""
        cmd = ReferenceScreenshotCommand()

        assert cmd.matches("take screenshot") is False
        assert cmd.matches("screen") is False


class TestReferenceScreenshotCommandExtractNumber(unittest.TestCase):
    """Test ReferenceScreenshotCommand number extraction."""

    def test_extract_number_explicit(self):
        """Test extracting explicit number."""
        cmd = ReferenceScreenshotCommand()

        assert cmd._extract_number("reference screenshot 2") == 2
        assert cmd._extract_number("screenshot 5") == 5

    def test_extract_number_default(self):
        """Test default number when not specified."""
        cmd = ReferenceScreenshotCommand()

        assert cmd._extract_number("reference screenshot") == 1
        assert cmd._extract_number("latest screenshot") == 1


class TestReferenceScreenshotCommandIsMultiRequest(unittest.TestCase):
    """Test ReferenceScreenshotCommand multi-request detection."""

    def test_is_multi_request_true(self):
        """Test detecting multi-screenshot request."""
        cmd = ReferenceScreenshotCommand()

        is_multi, count = cmd._is_multi_request("screenshot last 3")
        assert is_multi is True
        assert count == 3

        is_multi, count = cmd._is_multi_request("reference screenshot last 10")
        assert is_multi is True
        assert count == 10

    def test_is_multi_request_false(self):
        """Test detecting single screenshot request."""
        cmd = ReferenceScreenshotCommand()

        is_multi, count = cmd._is_multi_request("reference screenshot 2")
        assert is_multi is False
        assert count == 1


class TestReferenceScreenshotCommandExecute(BaseCommandTest):
    """Test ReferenceScreenshotCommand execution."""

    @patch('pathlib.Path.exists', return_value=False)
    def test_execute_no_directory(self, mock_exists):
        """Test execution when screenshots directory doesn't exist."""
        cmd = ReferenceScreenshotCommand()
        result = cmd.execute(self.context, "reference screenshot")

        assert result is None

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.glob', return_value=[])
    def test_execute_no_screenshots(self, mock_glob, mock_exists):
        """Test execution when no screenshots found."""
        cmd = ReferenceScreenshotCommand()
        result = cmd.execute(self.context, "reference screenshot")

        assert result is None

    def test_execute_single_screenshot(self):
        """Test executing single screenshot reference."""
        cmd = ReferenceScreenshotCommand()

        # Mock screenshot files
        mock_file1 = Mock(spec=Path)
        mock_file1.stat.return_value.st_mtime = 100
        mock_file1.absolute.return_value = Path("/path/to/screenshot_1.png")
        mock_file1.name = "screenshot_1.png"

        mock_file2 = Mock(spec=Path)
        mock_file2.stat.return_value.st_mtime = 200
        mock_file2.absolute.return_value = Path("/path/to/screenshot_2.png")
        mock_file2.name = "screenshot_2.png"

        with patch.object(cmd.screenshots_dir, 'exists', return_value=True), \
             patch.object(cmd.screenshots_dir, 'glob', return_value=[mock_file1, mock_file2]):

            result = cmd.execute(self.context, "reference screenshot")

            # Should return most recent (file2)
            assert result == str(Path("/path/to/screenshot_2.png"))

    def test_execute_single_screenshot_by_index(self):
        """Test executing single screenshot reference with index."""
        cmd = ReferenceScreenshotCommand()

        # Mock screenshot files
        mock_file1 = Mock(spec=Path)
        mock_file1.stat.return_value.st_mtime = 100
        mock_file1.absolute.return_value = Path("/path/to/screenshot_1.png")
        mock_file1.name = "screenshot_1.png"

        mock_file2 = Mock(spec=Path)
        mock_file2.stat.return_value.st_mtime = 200
        mock_file2.absolute.return_value = Path("/path/to/screenshot_2.png")
        mock_file2.name = "screenshot_2.png"

        with patch.object(cmd.screenshots_dir, 'exists', return_value=True), \
             patch.object(cmd.screenshots_dir, 'glob', return_value=[mock_file1, mock_file2]):

            result = cmd.execute(self.context, "reference screenshot 2")

            # Should return second most recent (file1)
            assert result == str(Path("/path/to/screenshot_1.png"))

    def test_execute_single_screenshot_invalid_index(self):
        """Test executing single screenshot reference with invalid index."""
        cmd = ReferenceScreenshotCommand()

        # Mock screenshot files
        mock_file1 = Mock(spec=Path)
        mock_file1.stat.return_value.st_mtime = 100
        mock_file1.absolute.return_value = Path("/path/to/screenshot_1.png")

        with patch.object(cmd.screenshots_dir, 'exists', return_value=True), \
             patch.object(cmd.screenshots_dir, 'glob', return_value=[mock_file1]):

            result = cmd.execute(self.context, "reference screenshot 5")

            # Index out of range
            assert result is None

    def test_execute_multiple_screenshots(self):
        """Test executing multiple screenshot reference."""
        cmd = ReferenceScreenshotCommand()

        # Mock screenshot files
        mock_file1 = Mock(spec=Path)
        mock_file1.stat.return_value.st_mtime = 100
        mock_file1.absolute.return_value = Path("/path/to/screenshot_1.png")

        mock_file2 = Mock(spec=Path)
        mock_file2.stat.return_value.st_mtime = 200
        mock_file2.absolute.return_value = Path("/path/to/screenshot_2.png")

        mock_file3 = Mock(spec=Path)
        mock_file3.stat.return_value.st_mtime = 300
        mock_file3.absolute.return_value = Path("/path/to/screenshot_3.png")

        with patch.object(cmd.screenshots_dir, 'exists', return_value=True), \
             patch.object(cmd.screenshots_dir, 'glob', return_value=[mock_file1, mock_file2, mock_file3]):

            result = cmd.execute(self.context, "screenshot last 2")

            # Should return 2 most recent files (file3, file2)
            expected = str(Path("/path/to/screenshot_3.png")) + "\n" + str(Path("/path/to/screenshot_2.png"))
            assert result == expected

    def test_execute_multiple_screenshots_limited(self):
        """Test executing multiple screenshots when fewer are available."""
        cmd = ReferenceScreenshotCommand()

        # Mock screenshot files
        mock_file1 = Mock(spec=Path)
        mock_file1.stat.return_value.st_mtime = 100
        mock_file1.absolute.return_value = Path("/path/to/screenshot_1.png")

        with patch.object(cmd.screenshots_dir, 'exists', return_value=True), \
             patch.object(cmd.screenshots_dir, 'glob', return_value=[mock_file1]):

            result = cmd.execute(self.context, "screenshot last 5")

            # Only 1 file available
            assert result == str(Path("/path/to/screenshot_1.png"))


class TestReferenceScreenshotCommandProperties(unittest.TestCase):
    """Test ReferenceScreenshotCommand properties."""

    def test_priority(self):
        """Test reference screenshot command priority."""
        cmd = ReferenceScreenshotCommand()
        assert cmd.priority == PRIORITY_MEDIUM

    def test_description(self):
        """Test reference screenshot command description."""
        cmd = ReferenceScreenshotCommand()
        assert "screenshot" in cmd.description.lower()

    def test_examples(self):
        """Test reference screenshot command examples."""
        cmd = ReferenceScreenshotCommand()
        assert len(cmd.examples) > 0
