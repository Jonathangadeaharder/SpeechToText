"""Screenshot command implementations."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyautogui

from src.commands.base import Command, CommandContext, PRIORITY_MEDIUM


class ScreenshotCommand(Command):
    """
    Take a screenshot and save it to the Screenshots folder.

    Creates a timestamped screenshot in the user's Pictures/Screenshots directory.
    """

    def __init__(self):
        """Initialize screenshot command."""
        self.logger = logging.getLogger("ScreenshotCommand")

        # Determine screenshots directory
        user_home = Path.home()
        self.screenshots_dir = user_home / "Pictures" / "Screenshots"

        # Create directory if it doesn't exist
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Screenshots directory: {self.screenshots_dir}")

    def matches(self, text: str) -> bool:
        """Check if text matches screenshot command."""
        text_clean = self.strip_punctuation(text)
        return text_clean in [
            "screenshot",
            "take screenshot",
            "screen shot",
            "green shot",  # Common transcription error
            "take green shot",
            "greenshot"
        ]

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Take and save a screenshot."""
        try:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = self.screenshots_dir / filename

            # Take screenshot
            self.logger.info(f"Taking screenshot: {filepath}")
            screenshot = pyautogui.screenshot()

            # Save screenshot
            screenshot.save(str(filepath))
            self.logger.info(f"Screenshot saved: {filepath}")

            # Optional: Show notification (if desired)
            print(f"Screenshot saved: {filename}")

            return None  # No text to type

        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            print(f"Error taking screenshot: {e}")
            return None

    @property
    def priority(self) -> int:
        return PRIORITY_MEDIUM

    @property
    def description(self) -> str:
        return "Take a screenshot and save to Pictures/Screenshots"

    @property
    def examples(self) -> list[str]:
        return ["screenshot", "take screenshot", "green shot"]


class ReferenceScreenshotCommand(Command):
    """
    Find a screenshot by index and paste its file path.

    Searches the Screenshots folder for screenshots and types the absolute path
    of the Nth most recent screenshot (1 = latest, 2 = second latest, etc.).
    """

    def __init__(self):
        """Initialize reference screenshot command."""
        self.logger = logging.getLogger("ReferenceScreenshotCommand")

        # Determine screenshots directory
        user_home = Path.home()
        self.screenshots_dir = user_home / "Pictures" / "Screenshots"

        # Regex patterns to match command
        # Pattern 1: Single screenshot - "reference screenshot 2" or "screenshot"
        self.single_pattern = re.compile(
            r"^(?:reference|paste|latest)?\s*(?:screenshot|screen\s*shot|green\s*shot|greenshot)\s*(?:path|file)?\s*(\d+)?$",
            re.IGNORECASE
        )

        # Pattern 2: Multiple screenshots - "reference screenshot last 3"
        self.multi_pattern = re.compile(
            r"^(?:reference|paste|latest)?\s*(?:screenshot|screen\s*shot|green\s*shot|greenshot)\s*(?:path|file)?\s*last\s+(\d+)$",
            re.IGNORECASE
        )

    def matches(self, text: str) -> bool:
        """Check if text matches reference screenshot command."""
        text_clean = self.strip_punctuation(text)
        return bool(self.single_pattern.match(text_clean) or self.multi_pattern.match(text_clean))

    def _is_multi_request(self, text: str) -> tuple[bool, int]:
        """
        Check if this is a "last N" request for multiple screenshots.

        Args:
            text: Command text

        Returns:
            Tuple of (is_multi, count) where is_multi indicates if it's a
            "last N" request and count is the number requested
        """
        text_clean = self.strip_punctuation(text)
        match = self.multi_pattern.match(text_clean)
        if match and match.group(1):
            return (True, int(match.group(1)))
        return (False, 1)

    def _extract_number(self, text: str) -> int:
        """
        Extract screenshot index from text (for single screenshot requests).

        Args:
            text: Command text (e.g., "reference screenshot 2")

        Returns:
            Screenshot index (1 for latest, 2 for second latest, etc.)
            Defaults to 1 if no number specified.
        """
        text_clean = self.strip_punctuation(text)
        match = self.single_pattern.match(text_clean)
        if match and match.group(1):
            return int(match.group(1))
        return 1  # Default to latest

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Find screenshot(s) and return path(s) to be typed."""
        try:
            # Check if screenshots directory exists
            if not self.screenshots_dir.exists():
                self.logger.warning(f"Screenshots directory does not exist: {self.screenshots_dir}")
                print("No screenshots directory found")
                return None

            # Find all screenshot files
            screenshot_files = list(self.screenshots_dir.glob("screenshot_*.png"))

            if not screenshot_files:
                self.logger.warning("No screenshots found in directory")
                print("No screenshots found")
                return None

            # Sort by modification time (most recent first)
            screenshot_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            # Check if this is a multi-screenshot request
            is_multi, count = self._is_multi_request(text)

            if is_multi:
                # Return multiple screenshot paths
                return self._get_multiple_screenshots(screenshot_files, count)
            else:
                # Return single screenshot path
                index = self._extract_number(text)
                return self._get_single_screenshot(screenshot_files, index)

        except Exception as e:
            self.logger.error(f"Failed to find screenshot: {e}")
            print(f"Error finding screenshot: {e}")
            return None

    def _get_single_screenshot(self, screenshot_files: list, index: int) -> Optional[str]:
        """
        Get a single screenshot path.

        Args:
            screenshot_files: Sorted list of screenshot files
            index: Screenshot index (1-based)

        Returns:
            Screenshot path or None
        """
        # Check if index is valid
        if index < 1 or index > len(screenshot_files):
            self.logger.warning(f"Invalid screenshot index: {index} (available: 1-{len(screenshot_files)})")
            print(f"Screenshot #{index} not found (only {len(screenshot_files)} available)")
            return None

        # Get the Nth screenshot (index is 1-based, list is 0-based)
        selected_screenshot = screenshot_files[index - 1]

        # Get absolute path
        screenshot_path = str(selected_screenshot.absolute())

        self.logger.info(f"Found screenshot #{index}: {screenshot_path}")
        print(f"Pasting path: {selected_screenshot.name}")

        return screenshot_path

    def _get_multiple_screenshots(self, screenshot_files: list, count: int) -> Optional[str]:
        """
        Get multiple screenshot paths.

        Args:
            screenshot_files: Sorted list of screenshot files
            count: Number of screenshots to get

        Returns:
            Screenshot paths separated by newlines, or None
        """
        # Limit count to available files
        actual_count = min(count, len(screenshot_files))

        if actual_count < count:
            self.logger.warning(f"Requested {count} screenshots but only {actual_count} available")
            print(f"Only {actual_count} screenshots available (requested {count})")

        # Get the last N screenshots
        selected_screenshots = screenshot_files[:actual_count]

        # Get absolute paths
        screenshot_paths = [str(f.absolute()) for f in selected_screenshots]

        # Join with newlines
        result = "\n".join(screenshot_paths)

        self.logger.info(f"Found last {actual_count} screenshots")
        print(f"Pasting paths of last {actual_count} screenshots")

        return result

    @property
    def priority(self) -> int:
        return PRIORITY_MEDIUM

    @property
    def description(self) -> str:
        return "Paste screenshot path(s) - single: 'screenshot 2', multiple: 'screenshot last 3'"

    @property
    def examples(self) -> list[str]:
        return ["reference screenshot", "reference screenshot 2", "screenshot last 3", "green shot last 5"]
