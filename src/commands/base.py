"""Base classes for the command pattern system."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pynput import keyboard, mouse

from src.core.config import Config


# Priority constants for commands (avoiding magic numbers)
PRIORITY_CRITICAL = 1000  # Critical system commands (help, exit, stop)
PRIORITY_HIGH = 500       # Specific multi-word commands
PRIORITY_MEDIUM = 200     # Common commands with specific triggers
PRIORITY_NORMAL = 100     # Basic single-word commands
PRIORITY_LOW = 50         # Fallback/general commands
PRIORITY_DEFAULT = 0      # Default/catch-all commands


@dataclass
class CommandContext:
    """
    Context object passed to commands during execution.

    Contains all dependencies commands might need to execute their actions.

    Attributes:
        config: Configuration object
        keyboard_controller: Keyboard controller for input simulation
        mouse_controller: Mouse controller for cursor/click control
        overlay_manager: Manager for UI overlays (grid, elements, etc.)
        text_processor: Text processor for handling last text operations
        event_bus: Event bus for publishing command events
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        data: Additional context data specific to command execution
    """

    config: Config
    keyboard_controller: keyboard.Controller
    mouse_controller: mouse.Controller
    overlay_manager: Any = None  # Type will be defined when OverlayManager is created
    text_processor: Any = None  # Type: TextProcessor
    event_bus: Any = None  # Type: EventBus
    screen_width: int = 1920
    screen_height: int = 1080
    data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize data dict if not provided."""
        if self.data is None:
            self.data = {}


class Command(ABC):
    """
    Abstract base class for all commands.

    Commands follow the Command Pattern, encapsulating actions as objects.
    Each command knows how to:
    1. Match against text input (matches)
    2. Execute the action (execute)
    3. Provide priority for ordering (priority)
    4. Describe itself for help/documentation (description, examples)

    Example:
        ```python
        class ClickCommand(Command):
            def matches(self, text: str) -> bool:
                return text.lower().startswith("click")

            def execute(self, context: CommandContext) -> Optional[str]:
                # Parse number from text and click
                number = self._extract_number(text)
                context.mouse_controller.click(...)
                return None  # No text to type

            @property
            def priority(self) -> int:
                return 100  # Higher priority = checked first

            @property
            def description(self) -> str:
                return "Click on numbered element"

            @property
            def examples(self) -> list[str]:
                return ["click 5", "click number 12"]
        ```
    """

    @abstractmethod
    def matches(self, text: str) -> bool:
        """
        Check if this command matches the given text.

        Args:
            text: Transcribed text from speech recognition

        Returns:
            True if this command should handle the text, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """
        Execute the command with the given context.

        Args:
            context: Command execution context with dependencies
            text: The matched text that triggered this command

        Returns:
            Optional text to type after command execution (None if no text)

        Raises:
            CommandExecutionError: If command execution fails
        """
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Command priority for ordering.

        Commands are checked in priority order (highest first).
        Use priority to ensure more specific commands are checked before
        more general ones.

        Suggested ranges:
        - 1000+: Critical system commands (help, exit, stop)
        - 500-999: Specific multi-word commands (e.g., "click number 5")
        - 100-499: Common single-word commands (e.g., "click", "scroll")
        - 1-99: Fallback/general commands
        - 0: Default/catch-all commands

        Returns:
            Integer priority (higher = checked first)
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what the command does.

        Used for help text and documentation.

        Returns:
            Brief description string
        """
        pass

    @property
    def examples(self) -> list[str]:
        """
        Example usage strings for this command.

        Used for help text and documentation.

        Returns:
            List of example command phrases
        """
        return []

    @property
    def enabled(self) -> bool:
        """
        Whether this command is enabled.

        Can be overridden to disable commands based on configuration,
        platform, or runtime conditions.

        Returns:
            True if command is enabled (default), False otherwise
        """
        return True

    def validate(self, context: CommandContext, text: str) -> bool:
        """
        Validate that command can be executed with given context.

        Override this to add pre-execution validation (e.g., check if
        required dependencies are available, overlay is shown, etc.).

        Args:
            context: Command execution context
            text: The matched text

        Returns:
            True if command can execute (default), False to skip execution
        """
        return True

    @staticmethod
    def strip_punctuation(text: str) -> str:
        """
        Strip punctuation and symbols from text for command matching.

        Removes common punctuation marks that may appear due to speech
        recognition errors or natural speech patterns.

        Args:
            text: Text to clean

        Returns:
            Text with punctuation removed, lowercased and stripped

        Example:
            >>> Command.strip_punctuation("screenshot!")
            "screenshot"
            >>> Command.strip_punctuation("click?")
            "click"
        """
        # Remove common punctuation marks
        # Keep hyphens and apostrophes as they may be part of commands
        punctuation_to_remove = '.!?,;:"""''(){}[]<>/@#$%^&*+=~`|\\'
        for char in punctuation_to_remove:
            text = text.replace(char, '')
        return text.lower().strip()


class CommandExecutionError(Exception):
    """Exception raised when command execution fails."""

    def __init__(self, command_name: str, message: str):
        """
        Initialize command execution error.

        Args:
            command_name: Name of the command that failed
            message: Error message describing what went wrong
        """
        self.command_name = command_name
        self.message = message
        super().__init__(f"{command_name}: {message}")
