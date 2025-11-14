"""Command registry for managing and executing voice commands."""

import logging
from typing import List, Optional, Tuple

from src.commands.base import Command, CommandContext, CommandExecutionError
from src.core.events import Event, EventBus, EventType


class CommandRegistry:
    """
    Central registry for managing and executing commands.

    The registry:
    1. Stores registered commands
    2. Finds matching commands by priority
    3. Executes commands with validation
    4. Publishes events for command lifecycle

    Example:
        ```python
        registry = CommandRegistry(event_bus)

        # Register commands
        registry.register(ClickCommand())
        registry.register(ScrollCommand())

        # Process voice input
        result, executed = registry.process("click 5", context)
        if result:
            logger.info(f"Command produced text: {result}")
        ```
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the command registry.

        Args:
            event_bus: Optional event bus for publishing command events
        """
        self.commands: List[Command] = []
        self.event_bus = event_bus
        self.logger = logging.getLogger("CommandRegistry")

    def register(self, command: Command) -> None:
        """
        Register a command with the registry.

        Commands are automatically sorted by priority (highest first).

        Args:
            command: Command instance to register
        """
        self.commands.append(command)
        # Keep commands sorted by priority (highest first)
        self.commands.sort(key=lambda c: c.priority, reverse=True)
        self.logger.debug(
            f"Registered command: {command.__class__.__name__} "
            f"(priority: {command.priority})"
        )

    def unregister(self, command: Command) -> bool:
        """
        Unregister a command from the registry.

        Args:
            command: Command instance to unregister

        Returns:
            True if command was found and removed, False otherwise
        """
        if command in self.commands:
            self.commands.remove(command)
            self.logger.debug(f"Unregistered command: {command.__class__.__name__}")
            return True
        return False

    def clear(self) -> None:
        """Clear all registered commands."""
        count = len(self.commands)
        self.commands.clear()
        self.logger.debug(f"Cleared {count} commands from registry")

    def get_commands(self, enabled_only: bool = True) -> List[Command]:
        """
        Get list of registered commands.

        Args:
            enabled_only: If True, return only enabled commands

        Returns:
            List of commands (sorted by priority)
        """
        if enabled_only:
            return [cmd for cmd in self.commands if cmd.enabled]
        return self.commands.copy()

    def find_matching_command(self, text: str, enabled_only: bool = True) -> Optional[Command]:
        """
        Find the first command that matches the given text.

        Commands are checked in priority order (highest first).

        Args:
            text: Text to match against commands
            enabled_only: If True, only check enabled commands

        Returns:
            First matching command, or None if no match
        """
        commands = self.get_commands(enabled_only=enabled_only)

        for command in commands:
            try:
                if command.matches(text):
                    self.logger.debug(
                        f"Command matched: {command.__class__.__name__} "
                        f"(priority: {command.priority})"
                    )
                    return command
            except Exception as e:
                self.logger.error(
                    f"Error in {command.__class__.__name__}.matches(): {e}"
                )

        self.logger.debug(f"No command matched text: '{text}'")
        return None

    def process(
        self,
        text: str,
        context: CommandContext,
        enabled_only: bool = True
    ) -> Tuple[Optional[str], bool]:
        """
        Process text and execute matching command.

        Workflow:
        1. Find matching command (by priority)
        2. Validate command can execute
        3. Execute command
        4. Publish events to event bus
        5. Return result

        Args:
            text: Voice input text to process
            context: Command execution context
            enabled_only: If True, only check enabled commands

        Returns:
            Tuple of (result_text, command_executed)
            - result_text: Text returned from command (None if no text)
            - command_executed: True if command was found and executed

        Raises:
            CommandExecutionError: If command execution fails
        """
        # Find matching command
        command = self.find_matching_command(text, enabled_only=enabled_only)
        if not command:
            return None, False

        # Publish COMMAND_DETECTED event
        if self.event_bus:
            self.event_bus.publish(
                Event(
                    EventType.COMMAND_DETECTED,
                    {
                        "command_class": command.__class__.__name__,
                        "text": text,
                        "priority": command.priority,
                    }
                )
            )

        # Validate command
        try:
            if not command.validate(context, text):
                self.logger.warning(
                    f"Command validation failed: {command.__class__.__name__}"
                )
                if self.event_bus:
                    self.event_bus.publish(
                        Event(
                            EventType.COMMAND_FAILED,
                            {
                                "command_class": command.__class__.__name__,
                                "text": text,
                                "reason": "validation_failed",
                            }
                        )
                    )
                return None, False
        except Exception as e:
            self.logger.error(
                f"Error validating {command.__class__.__name__}: {e}"
            )
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        EventType.COMMAND_FAILED,
                        {
                            "command_class": command.__class__.__name__,
                            "text": text,
                            "reason": "validation_error",
                            "error": str(e),
                        }
                    )
                )
            return None, False

        # Execute command
        try:
            self.logger.info(
                f"Executing command: {command.__class__.__name__} "
                f"with text: '{text}'"
            )
            result = command.execute(context, text)

            # Publish COMMAND_EXECUTED event
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        EventType.COMMAND_EXECUTED,
                        {
                            "command_class": command.__class__.__name__,
                            "text": text,
                            "result": result,
                        }
                    )
                )

            return result, True

        except CommandExecutionError as e:
            self.logger.error(f"Command execution failed: {e}")
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        EventType.COMMAND_FAILED,
                        {
                            "command_class": command.__class__.__name__,
                            "text": text,
                            "reason": "execution_error",
                            "error": str(e),
                        }
                    )
                )
            raise

        except Exception as e:
            self.logger.error(
                f"Unexpected error executing {command.__class__.__name__}: {e}"
            )
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        EventType.COMMAND_FAILED,
                        {
                            "command_class": command.__class__.__name__,
                            "text": text,
                            "reason": "unexpected_error",
                            "error": str(e),
                        }
                    )
                )
            raise CommandExecutionError(command.__class__.__name__, str(e))

    def get_command_count(self, enabled_only: bool = True) -> int:
        """
        Get the number of registered commands.

        Args:
            enabled_only: If True, count only enabled commands

        Returns:
            Number of commands
        """
        return len(self.get_commands(enabled_only=enabled_only))

    def get_help_text(self, enabled_only: bool = True) -> str:
        """
        Generate help text listing all commands.

        Args:
            enabled_only: If True, only include enabled commands

        Returns:
            Formatted help text with command descriptions and examples
        """
        commands = self.get_commands(enabled_only=enabled_only)

        if not commands:
            return "No commands registered."

        lines = ["Available Commands:", ""]

        for command in commands:
            lines.append(f"• {command.description}")
            if command.examples:
                examples_str = ", ".join(f'"{ex}"' for ex in command.examples)
                lines.append(f"  Examples: {examples_str}")
            lines.append(f"  Priority: {command.priority}")
            lines.append("")

        return "\n".join(lines)
