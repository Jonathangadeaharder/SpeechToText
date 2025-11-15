"""Mouse command implementations."""

import time
from typing import Any, Dict, Optional

from pynput import mouse

from src.commands.base import (
    Command,
    CommandContext,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_NORMAL,
)
from src.commands.parser import CommandParser
from src.core.events import Event, EventType


def publish_command_event(context: CommandContext, command_name: str, event_data: Dict[str, Any]) -> None:
    """
    Publish command executed event (DRY helper).

    Args:
        context: Command execution context
        command_name: Name of the command
        event_data: Additional event data
    """
    if context.event_bus:
        context.event_bus.publish(
            Event(EventType.COMMAND_EXECUTED, {**event_data, "command": command_name})
        )


class ClickCommand(Command):
    """Left click at current mouse position."""

    def matches(self, text: str) -> bool:
        return self.strip_punctuation(text) == "click"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute left click."""
        context.mouse_controller.click(mouse.Button.left, 1)
        publish_command_event(context, "ClickCommand", {"button": "left", "text": text})
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_NORMAL

    @property
    def description(self) -> str:
        return "Left click at current mouse position"

    @property
    def examples(self) -> list[str]:
        return ["click"]


class RightClickCommand(Command):
    """Right click at current mouse position."""

    def matches(self, text: str) -> bool:
        return self.strip_punctuation(text) == "right click"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute right click."""
        context.mouse_controller.click(mouse.Button.right, 1)
        publish_command_event(context, "RightClickCommand", {"button": "right", "text": text})
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_MEDIUM  # Higher than generic click

    @property
    def description(self) -> str:
        return "Right click at current mouse position"

    @property
    def examples(self) -> list[str]:
        return ["right click"]


class DoubleClickCommand(Command):
    """Double click at current mouse position."""

    def matches(self, text: str) -> bool:
        return self.strip_punctuation(text) == "double click"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute double click."""
        context.mouse_controller.click(mouse.Button.left, 2)
        publish_command_event(context, "DoubleClickCommand", {"button": "left", "count": 2, "text": text})
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_MEDIUM  # Higher than generic click

    @property
    def description(self) -> str:
        return "Double click at current mouse position"

    @property
    def examples(self) -> list[str]:
        return ["double click"]


class MiddleClickCommand(Command):
    """Middle click at current mouse position."""

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean in ["middle click", "wheel click"]

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute middle click."""
        context.mouse_controller.click(mouse.Button.middle, 1)
        publish_command_event(context, "MiddleClickCommand", {"button": "middle", "text": text})
        return None

    @property
    def priority(self) -> int:
        return 200

    @property
    def description(self) -> str:
        return "Middle click at current mouse position"

    @property
    def examples(self) -> list[str]:
        return ["middle click", "wheel click"]


class ScrollCommand(Command):
    """
    Scroll up/down/left/right.

    Supports exponential scaling when repeated.
    """

    def __init__(self):
        """Initialize scroll command."""
        self._last_direction = None
        self._repeat_count = 0
        self._base_scroll = 3

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean.startswith("scroll") and any(
            direction in text_clean for direction in ["up", "down", "left", "right"]
        )

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute scroll."""
        text_clean = self.strip_punctuation(text)

        # Determine direction
        if "up" in text_clean:
            direction = "up"
            dx, dy = 0, -self._base_scroll
        elif "down" in text_clean:
            direction = "down"
            dx, dy = 0, self._base_scroll
        elif "left" in text_clean:
            direction = "left"
            dx, dy = -self._base_scroll, 0
        elif "right" in text_clean:
            direction = "right"
            dx, dy = self._base_scroll, 0
        else:
            return None

        # Calculate exponential scaling for repeated commands
        if self._last_direction == direction:
            self._repeat_count += 1
        else:
            self._repeat_count = 0
            self._last_direction = direction

        # Exponential scaling: 3, 6, 12, 24, capped at 48
        multiplier = min(2 ** self._repeat_count, 16)
        final_dx = dx * multiplier
        final_dy = dy * multiplier

        # Perform scroll
        context.mouse_controller.scroll(final_dx, final_dy)
        publish_command_event(
            context,
            "ScrollCommand",
            {"direction": direction, "multiplier": multiplier, "text": text}
        )
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_NORMAL

    @property
    def description(self) -> str:
        return "Scroll in specified direction (with exponential scaling when repeated)"

    @property
    def examples(self) -> list[str]:
        return ["scroll up", "scroll down", "scroll left", "scroll right"]


class MouseMoveCommand(Command):
    """
    Move mouse cursor up/down/left/right.

    Supports exponential scaling when repeated.
    Note: In original implementation, "move left/right" handled window snapping.
    This command only handles up/down movement.
    """

    def __init__(self):
        """Initialize mouse move command."""
        self._last_direction = None
        self._repeat_count = 0
        self._base_step = 50

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        # Only match "move up" and "move down" (left/right are window commands)
        return text_clean.startswith("move") and any(
            direction in text_clean for direction in ["up", "down"]
        )

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute mouse movement."""
        text_clean = self.strip_punctuation(text)

        # Determine direction (only up/down for mouse movement)
        if "up" in text_clean:
            direction = "up"
        elif "down" in text_clean:
            direction = "down"
        else:
            return None

        # Calculate exponential scaling for repeated commands
        if self._last_direction == direction:
            self._repeat_count += 1
        else:
            self._repeat_count = 0
            self._last_direction = direction

        # Exponential scaling: base * 2^count, capped at 800px
        step_size = min(self._base_step * (2 ** self._repeat_count), 800)

        # Get current position
        current_x, current_y = context.mouse_controller.position

        # Calculate new position
        if direction == "up":
            new_y = max(0, current_y - step_size)
        else:  # down
            new_y = min(context.screen_height - 1, current_y + step_size)

        # Move mouse
        context.mouse_controller.position = (current_x, new_y)
        publish_command_event(
            context,
            "MouseMoveCommand",
            {
                "direction": direction,
                "step_size": step_size,
                "multiplier": 2 ** self._repeat_count,
                "new_position": (current_x, new_y),
                "text": text
            }
        )
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_NORMAL

    @property
    def description(self) -> str:
        return "Move mouse cursor up/down (with exponential scaling when repeated)"

    @property
    def examples(self) -> list[str]:
        return ["move up", "move down"]


class ClickNumberCommand(Command):
    """
    Click on a numbered element from overlay.

    Requires parser to extract numbers.
    """

    def __init__(self, parser: CommandParser):
        """
        Initialize click number command.

        Args:
            parser: Command parser for extracting numbers
        """
        self.parser = parser

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean.startswith("click") and self.parser.contains_numbers(text_clean)

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute click on numbered element."""
        # Extract number from command
        numbers = self.parser.extract_numbers(text)
        if not numbers:
            return None

        number = numbers[0]

        # Check if overlay is available
        if not context.overlay_manager:
            return None

        # Get element position from overlay
        position = context.overlay_manager.get_element_position(number)
        if not position:
            # No element with this number
            publish_command_event(
                context,
                "ClickNumberCommand",
                {"number": number, "text": text, "error": "element_not_found"}
            )
            return None

        # Click at the element position
        x, y = position
        context.mouse_controller.position = (x, y)
        context.mouse_controller.click(mouse.Button.left, 1)

        publish_command_event(
            context,
            "ClickNumberCommand",
            {"number": number, "x": x, "y": y, "text": text}
        )
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_HIGH  # High priority - very specific command

    @property
    def description(self) -> str:
        return "Click on numbered overlay element"

    @property
    def examples(self) -> list[str]:
        return ["click 5", "click number 12", "click two"]


class MoveToNumberCommand(Command):
    """
    Move mouse to a numbered element from grid overlay (without clicking).

    When grid is visible and user says just a number (e.g., "5"),
    moves the mouse to that cell's center.
    """

    def __init__(self, parser: CommandParser):
        """
        Initialize move to number command.

        Args:
            parser: Command parser for extracting numbers
        """
        self.parser = parser

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)

        # Match if text is just a number (or word representation)
        # But NOT if it starts with a command word like "click", "refine", etc.
        command_prefixes = ["click", "refine", "type", "switch", "scroll", "move", "page"]

        # Check if text starts with any command prefix
        for prefix in command_prefixes:
            if text_clean.startswith(prefix):
                return False

        # Check if text contains a number
        return self.parser.contains_numbers(text_clean)

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Move mouse to numbered element."""
        # Extract number from command
        numbers = self.parser.extract_numbers(text)
        if not numbers:
            return None

        number = numbers[0]

        # Check if overlay is available
        if not context.overlay_manager:
            return None

        # Check if grid overlay is visible
        if not context.overlay_manager.is_any_overlay_visible():
            return None

        # Get element position from overlay
        position = context.overlay_manager.get_element_position(number)
        if not position:
            # No element with this number
            return None

        # Move mouse to the element position (don't click)
        x, y = position
        context.mouse_controller.position = (x, y)

        publish_command_event(
            context,
            "MoveToNumberCommand",
            {"number": number, "x": x, "y": y, "text": text}
        )
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_NORMAL  # Normal priority - fallback for numbers

    @property
    def description(self) -> str:
        return "Move mouse to numbered grid cell (without clicking)"

    @property
    def examples(self) -> list[str]:
        return ["5", "twelve", "45"]


class DragBetweenNumbersCommand(Command):
    """
    Click and drag from one numbered cell to another.

    When grid is visible and user says "NUMBER to NUMBER",
    clicks at first cell, drags to second cell, and releases.
    Useful for selecting text or creating drag operations.
    """

    def __init__(self, parser: CommandParser):
        """
        Initialize drag between numbers command.

        Args:
            parser: Command parser for extracting numbers
        """
        self.parser = parser

    def matches(self, text: str) -> bool:
        # Don't strip punctuation yet - we need to check for hyphens
        text_clean = text.lower().strip()

        # Match pattern: "NUMBER to NUMBER", "NUMBER two NUMBER", or "NUMBER-NUMBER"
        # Example: "5 to 9", "twenty to thirty", "5-9", "20-47"
        has_separator = " to " in text_clean or " two " in text_clean or "-" in text_clean

        if not has_separator:
            return False

        # Extract numbers and verify we have exactly 2
        numbers = self.parser.extract_numbers(text_clean)
        return len(numbers) == 2

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Click and drag from first number to second number."""
        # Extract numbers from command
        numbers = self.parser.extract_numbers(text)
        if len(numbers) != 2:
            return None

        start_num, end_num = numbers

        # Check if overlay is available
        if not context.overlay_manager:
            return None

        # Check if grid overlay is visible
        if not context.overlay_manager.is_any_overlay_visible():
            return None

        # Get start position
        start_pos = context.overlay_manager.get_element_position(start_num)
        if not start_pos:
            return None

        # Get end position
        end_pos = context.overlay_manager.get_element_position(end_num)
        if not end_pos:
            return None

        # Perform drag operation
        start_x, start_y = start_pos
        end_x, end_y = end_pos

        # Move to start position
        context.mouse_controller.position = (start_x, start_y)

        # Delay to ensure cursor is in position
        time.sleep(0.1)

        # Press and hold left button
        context.mouse_controller.press(mouse.Button.left)

        # Delay for system to register press
        time.sleep(0.15)

        # Move to end position (while holding)
        context.mouse_controller.position = (end_x, end_y)

        # Delay before release to ensure drag is registered
        time.sleep(0.15)

        # Release button
        context.mouse_controller.release(mouse.Button.left)

        publish_command_event(
            context,
            "DragBetweenNumbersCommand",
            {"start": start_num, "end": end_num, "text": text}
        )
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_HIGH  # High priority - specific pattern

    @property
    def description(self) -> str:
        return "Click and drag from one grid cell to another"

    @property
    def examples(self) -> list[str]:
        return ["5 to 9", "twenty to thirty", "45 to 52"]


class RefineGridCommand(Command):
    """
    Refine/zoom into a grid cell with 3x3 subdivision.

    When grid is visible and user says "refine [number]",
    zooms into that cell showing 9 smaller cells.
    """

    def __init__(self, parser: CommandParser):
        """
        Initialize refine grid command.

        Args:
            parser: Command parser for extracting numbers
        """
        self.parser = parser

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean.startswith("refine") and self.parser.contains_numbers(text_clean)

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Refine grid to zoom into a cell."""
        # Extract number from command
        numbers = self.parser.extract_numbers(text)
        if not numbers:
            return None

        number = numbers[0]

        # Check if overlay manager is available
        if not context.overlay_manager:
            return None

        # Get current overlay type
        from src.overlays.base import OverlayType
        overlay_type = context.overlay_manager.get_current_overlay_type()

        if overlay_type != OverlayType.GRID:
            # Grid not visible, can't refine
            return None

        # Get the grid overlay
        grid_overlay = context.overlay_manager._overlays.get(OverlayType.GRID)
        if not grid_overlay:
            return None

        # Refine the grid
        success = grid_overlay.refine_grid(number)

        if success:
            publish_command_event(
                context,
                "RefineGridCommand",
                {"cell_number": number, "text": text}
            )

        return None

    @property
    def priority(self) -> int:
        return PRIORITY_HIGH  # High priority - specific command

    @property
    def description(self) -> str:
        return "Zoom into grid cell with 3x3 subdivision"

    @property
    def examples(self) -> list[str]:
        return ["refine 5", "refine grid 45", "refine twelve"]
