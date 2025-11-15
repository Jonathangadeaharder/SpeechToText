"""Window management command implementations."""

import time
from typing import Optional

from pynput import keyboard

from src.commands.base import Command, CommandContext
from src.core.events import Event, EventType


class MoveWindowCommand(Command):
    """
    Snap window to left or right half of screen.

    Uses Win+Left or Win+Right keyboard shortcuts to snap windows.
    Automatically dismisses Windows Snap Assist by pressing Enter.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return (
            "move window left" in text_clean
            or "move left" in text_clean
            or "snap left" in text_clean
            or "move window right" in text_clean
            or "move right" in text_clean
            or "snap right" in text_clean
        )

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Snap window to left or right half."""
        text_clean = self.strip_punctuation(text)

        # Determine direction
        if "left" in text_clean:
            direction = "left"
            key = keyboard.Key.left
        else:  # right
            direction = "right"
            key = keyboard.Key.right

        # Press Win+Direction
        with context.keyboard_controller.pressed(keyboard.Key.cmd):
            context.keyboard_controller.press(key)
            context.keyboard_controller.release(key)

        # Dismiss Windows Snap Assist overlay (press Escape to dismiss without selecting)
        time.sleep(0.1)
        context.keyboard_controller.press(keyboard.Key.esc)
        context.keyboard_controller.release(keyboard.Key.esc)
        time.sleep(0.05)

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "MoveWindowCommand", "direction": direction, "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200  # Higher priority to match before mouse move

    @property
    def description(self) -> str:
        return "Snap window to left or right half of screen (Win+Left/Right)"

    @property
    def examples(self) -> list[str]:
        return ["move left", "move right", "move window left", "move window right", "snap left", "snap right"]


class MinimizeCommand(Command):
    """
    Minimize the current window.

    Uses Win+Down on Windows, Cmd+M on other platforms.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return "minimize" in text_clean or "minimise" in text_clean

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Minimize window."""
        # Windows: Win+Down, Others: Cmd+M
        import platform
        if platform.system() == "Windows":
            with context.keyboard_controller.pressed(keyboard.Key.cmd):
                context.keyboard_controller.press(keyboard.Key.down)
                context.keyboard_controller.release(keyboard.Key.down)
        else:
            with context.keyboard_controller.pressed(keyboard.Key.cmd):
                context.keyboard_controller.press("m")
                context.keyboard_controller.release("m")

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "MinimizeCommand", "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Minimize current window (Win+Down / Cmd+M)"

    @property
    def examples(self) -> list[str]:
        return ["minimize", "minimise"]


class MaximizeCommand(Command):
    """
    Maximize the current window.

    Uses Win+Up on Windows, Cmd+Up on other platforms.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return "maximize" in text_clean or "maximise" in text_clean

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Maximize window."""
        # Windows: Win+Up
        with context.keyboard_controller.pressed(keyboard.Key.cmd):
            context.keyboard_controller.press(keyboard.Key.up)
            context.keyboard_controller.release(keyboard.Key.up)

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "MaximizeCommand", "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Maximize current window (Win+Up)"

    @property
    def examples(self) -> list[str]:
        return ["maximize", "maximise"]


class CloseWindowCommand(Command):
    """
    Close the current window.

    Uses Alt+F4 keyboard shortcut.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean == "close" or "close window" in text_clean

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Close window."""
        # Alt+F4 to close window
        with context.keyboard_controller.pressed(keyboard.Key.alt):
            context.keyboard_controller.press(keyboard.Key.f4)
            context.keyboard_controller.release(keyboard.Key.f4)

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "CloseWindowCommand", "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Close current window (Alt+F4)"

    @property
    def examples(self) -> list[str]:
        return ["close", "close window"]


class SwitchWindowCommand(Command):
    """
    Switch between open windows.

    Uses Alt+Tab to switch to next window or Alt+Shift+Tab for previous.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return (
            text_clean == "switch"
            or "switch window" in text_clean
        )

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Switch windows."""
        text_clean = self.strip_punctuation(text)

        # Check for previous/back
        if "previous" in text_clean or "back" in text_clean:
            # Alt+Shift+Tab for previous window
            with context.keyboard_controller.pressed(keyboard.Key.alt):
                with context.keyboard_controller.pressed(keyboard.Key.shift):
                    context.keyboard_controller.press(keyboard.Key.tab)
                    context.keyboard_controller.release(keyboard.Key.tab)
            direction = "previous"
        else:
            # Alt+Tab for next window
            with context.keyboard_controller.pressed(keyboard.Key.alt):
                context.keyboard_controller.press(keyboard.Key.tab)
                context.keyboard_controller.release(keyboard.Key.tab)
            direction = "next"

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "SwitchWindowCommand", "direction": direction, "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Switch between windows (Alt+Tab)"

    @property
    def examples(self) -> list[str]:
        return ["switch", "switch window", "switch window previous"]


class CenterWindowCommand(Command):
    """
    Center the current window on screen.

    Note: This is a placeholder. Window centering requires platform-specific
    window management APIs. For now, we maximize and then restore to simulate centering.
    """

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return "center window" in text_clean or "centre window" in text_clean

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Center window (placeholder implementation)."""
        # This is a simplified implementation
        # True centering would require platform-specific window APIs

        # On Windows, we can't easily center without additional libraries
        # For now, this is a placeholder that could be enhanced later
        # with pywinauto or similar

        # Publish event
        if context.event_bus:
            context.event_bus.publish(
                Event(
                    EventType.COMMAND_EXECUTED,
                    {"command": "CenterWindowCommand", "text": text}
                )
            )

        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Center window on screen (placeholder)"

    @property
    def examples(self) -> list[str]:
        return ["center window", "centre window"]
