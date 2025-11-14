"""Navigation command implementations."""

from typing import Optional

from pynput import keyboard

from src.commands.base import Command, CommandContext
from src.core.events import Event, EventType


class ArrowKeyCommand(Command):
    """
    Press arrow keys (up, down, left, right).

    Single word commands for basic navigation.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        # Only match single word arrow keys
        return text_clean in ["left", "right", "up", "down"]

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Press arrow key."""
        text_clean = self.strip_punctuation(text)

        # Map text to keyboard key
        key_map = {
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
        }

        key = key_map[text_clean]
        context.keyboard_controller.press(key)
        context.keyboard_controller.release(key)

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "ArrowKeyCommand", "direction": text_clean, "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 150  # Standard priority for basic keys

    @property
    def description(self) -> str:
        return "Press arrow keys for navigation"

    @property
    def examples(self) -> list[str]:
        return ["left", "right", "up", "down"]


class PageNavigationCommand(Command):
    """
    Navigate by page (page up, page down).

    Uses Page Up and Page Down keyboard keys.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return "page up" in text_clean or "page down" in text_clean

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute page navigation."""
        text_clean = self.strip_punctuation(text)

        if "up" in text_clean:
            key = keyboard.Key.page_up
            direction = "up"
        else:  # down
            key = keyboard.Key.page_down
            direction = "down"

        context.keyboard_controller.press(key)
        context.keyboard_controller.release(key)

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "PageNavigationCommand", "direction": direction, "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200  # Higher than arrow keys to match first

    @property
    def description(self) -> str:
        return "Navigate by page (Page Up / Page Down)"

    @property
    def examples(self) -> list[str]:
        return ["page up", "page down"]


class HomeEndCommand(Command):
    """
    Jump to start or end of document/line.

    Supports:
    - "go to start/top/beginning" -> Ctrl+Home (document start)
    - "go to end/bottom" -> Ctrl+End (document end)
    - "line start" -> Home (line start)
    - "line end" -> End (line end)
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return (
            "go to start" in text_clean
            or "go to top" in text_clean
            or "go to beginning" in text_clean
            or "go to end" in text_clean
            or "go to bottom" in text_clean
            or text_clean == "line start"
            or text_clean == "line end"
        )

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute home/end navigation."""
        text_clean = self.strip_punctuation(text)

        # Determine action - check specific line commands first
        if text_clean == "line start":
            # Just Home for line start
            context.keyboard_controller.press(keyboard.Key.home)
            context.keyboard_controller.release(keyboard.Key.home)
            action = "line_start"
        elif text_clean == "line end":
            # Just End for line end
            context.keyboard_controller.press(keyboard.Key.end)
            context.keyboard_controller.release(keyboard.Key.end)
            action = "line_end"
        elif "start" in text_clean or "top" in text_clean or "beginning" in text_clean:
            # Ctrl+Home for document start
            with context.keyboard_controller.pressed(keyboard.Key.ctrl):
                context.keyboard_controller.press(keyboard.Key.home)
                context.keyboard_controller.release(keyboard.Key.home)
            action = "document_start"
        elif "end" in text_clean or "bottom" in text_clean:
            # Ctrl+End for document end
            with context.keyboard_controller.pressed(keyboard.Key.ctrl):
                context.keyboard_controller.press(keyboard.Key.end)
                context.keyboard_controller.release(keyboard.Key.end)
            action = "document_end"
        else:
            return None

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "HomeEndCommand", "action": action, "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200  # Higher priority for multi-word commands

    @property
    def description(self) -> str:
        return "Jump to start/end of document or line"

    @property
    def examples(self) -> list[str]:
        return [
            "go to start",
            "go to top",
            "go to end",
            "go to bottom",
            "line start",
            "line end",
        ]
