"""Overlay command implementations."""

from typing import Optional

from src.commands.base import Command, CommandContext
from src.overlays.base import OverlayType


class ShowGridCommand(Command):
    """
    Show numbered grid overlay on screen.

    Displays a 9x9 grid with numbered cells for mouse navigation.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean == "grid"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Show grid overlay."""
        # Check if overlay manager is available
        if not context.overlay_manager:
            return None

        # Show grid with 9x9 subdivisions
        context.overlay_manager.show_overlay(OverlayType.GRID, grid_size=9)

        # Note: CommandRegistry automatically publishes COMMAND_EXECUTED event
        # after execute() completes, so we don't need to publish it here

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Show 9x9 numbered grid overlay"

    @property
    def examples(self) -> list[str]:
        return ["grid"]


class ShowElementsCommand(Command):
    """
    Show numbered UI elements overlay.

    Detects clickable elements in the active window and displays numbers.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean == "numbers"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Show numbered elements overlay."""
        # Check if overlay manager is available
        if not context.overlay_manager:
            return None

        # Show numbered elements
        context.overlay_manager.show_overlay(OverlayType.ELEMENT)

        # Note: CommandRegistry automatically publishes COMMAND_EXECUTED event
        # after execute() completes, so we don't need to publish it here

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Show numbered UI elements overlay"

    @property
    def examples(self) -> list[str]:
        return ["numbers"]


class ShowWindowsCommand(Command):
    """
    Show numbered list of open windows.

    Enumerates all visible windows and displays them with numbers for selection.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean == "windows"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Show windows overlay."""
        # Check if overlay manager is available
        if not context.overlay_manager:
            return None

        # Show windows list
        context.overlay_manager.show_overlay(OverlayType.WINDOW)

        # Note: CommandRegistry automatically publishes COMMAND_EXECUTED event
        # after execute() completes, so we don't need to publish it here

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Show numbered list of open windows"

    @property
    def examples(self) -> list[str]:
        return ["windows"]


class HideOverlayCommand(Command):
    """
    Hide any visible overlay.

    Supports various speech recognition alternatives for robustness.
    Handles common misrecognitions like "height" instead of "hide".
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        # Simple single-word commands
        # "height" included as common misrecognition of "hide"
        return text_clean in ["hide", "height", "close"]

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Hide overlay."""
        # Check if overlay manager is available
        if not context.overlay_manager:
            return None

        # Hide overlay
        context.overlay_manager.hide_current_overlay()

        # Note: CommandRegistry automatically publishes COMMAND_EXECUTED event
        # after execute() completes, so we don't need to publish it here

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Hide visible overlay (grid, elements, windows, commands)"

    @property
    def examples(self) -> list[str]:
        return ["hide", "close"]


class ShowHelpCommand(Command):
    """
    Show help overlay with available commands.

    Displays categorized list of voice commands.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean in ["commands", "help"]

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Show help overlay."""
        # Check if overlay manager is available
        if not context.overlay_manager:
            return None

        # Show commands/help
        context.overlay_manager.show_overlay(OverlayType.HELP)

        # Note: CommandRegistry automatically publishes COMMAND_EXECUTED event
        # after execute() completes, so we don't need to publish it here

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Show help overlay with available commands"

    @property
    def examples(self) -> list[str]:
        return ["commands", "help"]
