"""
Integration tests for full command execution flow.

Tests the complete flow from text input through command detection,
validation, and execution.
"""

import pytest
from pynput import keyboard, mouse

from src.commands.base import Command, CommandContext
from src.commands.handlers.keyboard_commands import (
    ClipboardCommand,
    EnterCommand,
    SelectAllCommand,
    UndoCommand,
)
from src.commands.handlers.mouse_commands import (
    ClickCommand,
    DoubleClickCommand,
    RightClickCommand,
    ScrollCommand,
)
from src.commands.parser import CommandParser
from src.commands.registry import CommandRegistry
from src.core.config import Config
from src.core.events import EventBus, EventType


class MockKeyboardController:
    """Mock keyboard controller for testing."""

    def __init__(self):
        self.pressed_keys = []
        self.released_keys = []
        self.typed_text = []
        self.current_pressed = set()

    def press(self, key):
        self.pressed_keys.append(key)
        self.current_pressed.add(key)

    def release(self, key):
        self.released_keys.append(key)
        self.current_pressed.discard(key)

    def type(self, text):
        self.typed_text.append(text)

    def pressed(self, key):
        """Context manager for pressing a key."""

        class PressedContext:
            def __init__(self, controller, key):
                self.controller = controller
                self.key = key

            def __enter__(self):
                self.controller.press(self.key)
                return self

            def __exit__(self, *args):
                self.controller.release(self.key)
                return False

        return PressedContext(self, key)


class MockMouseController:
    """Mock mouse controller for testing."""

    def __init__(self):
        self.clicks = []
        self.scrolls = []
        self.position = (100, 100)

    def click(self, button, count=1):
        self.clicks.append((button, count))

    def scroll(self, dx, dy):
        self.scrolls.append((dx, dy))


@pytest.fixture
def config():
    """Create test configuration."""
    config = Config()
    config.config = {
        "text_processing": {
            "punctuation_commands": True,
            "punctuation_map": {"period": ".", "comma": ","},
            "custom_vocabulary": {},
            "command_words": {},
        },
        "advanced": {"log_level": "DEBUG"},
    }
    return config


@pytest.fixture
def event_bus():
    """Create event bus for testing."""
    return EventBus()


@pytest.fixture
def command_registry(event_bus):
    """Create command registry with common commands."""
    registry = CommandRegistry(event_bus)

    # Register keyboard commands
    registry.register(EnterCommand())
    registry.register(SelectAllCommand())
    registry.register(UndoCommand())
    registry.register(ClipboardCommand())

    # Register mouse commands
    registry.register(ClickCommand())
    registry.register(RightClickCommand())
    registry.register(DoubleClickCommand())
    registry.register(ScrollCommand())

    return registry


@pytest.fixture
def command_context(config, event_bus):
    """Create command context with mock controllers."""
    return CommandContext(
        config=config,
        keyboard_controller=MockKeyboardController(),
        mouse_controller=MockMouseController(),
        event_bus=event_bus,
        screen_width=1920,
        screen_height=1080,
    )


def test_enter_command_flow(command_registry, command_context, event_bus):
    """Test complete flow for Enter command."""
    # Track events
    events_received = []
    event_bus.subscribe(EventType.COMMAND_EXECUTED, lambda e: events_received.append(e))

    # Process "enter" text
    result, executed = command_registry.process("enter", command_context)

    # Verify command was executed
    assert executed
    assert result is None  # No text to type

    # Verify keyboard interaction
    kb = command_context.keyboard_controller
    assert keyboard.Key.enter in kb.pressed_keys
    assert keyboard.Key.enter in kb.released_keys

    # Verify event was published
    assert len(events_received) == 1
    assert events_received[0].event_type == EventType.COMMAND_EXECUTED


def test_clipboard_command_flow(command_registry, command_context):
    """Test clipboard operations (copy, cut, paste)."""
    kb = command_context.keyboard_controller

    # Test copy
    result, executed = command_registry.process("copy", command_context)
    assert executed
    assert keyboard.Key.ctrl in kb.current_pressed or keyboard.Key.ctrl in kb.pressed_keys
    assert "c" in kb.pressed_keys or "c" in kb.released_keys

    kb.__init__()  # Reset

    # Test paste
    result, executed = command_registry.process("paste", command_context)
    assert executed
    assert "v" in kb.pressed_keys or "v" in kb.released_keys


def test_mouse_click_flow(command_registry, command_context):
    """Test mouse click commands."""
    mouse_ctrl = command_context.mouse_controller

    # Test left click
    result, executed = command_registry.process("click", command_context)
    assert executed
    assert len(mouse_ctrl.clicks) == 1
    assert mouse_ctrl.clicks[0][0] == mouse.Button.left
    assert mouse_ctrl.clicks[0][1] == 1

    # Test right click
    result, executed = command_registry.process("right click", command_context)
    assert executed
    assert len(mouse_ctrl.clicks) == 2
    assert mouse_ctrl.clicks[1][0] == mouse.Button.right

    # Test double click
    result, executed = command_registry.process("double click", command_context)
    assert executed
    assert len(mouse_ctrl.clicks) == 3
    assert mouse_ctrl.clicks[2][0] == mouse.Button.left
    assert mouse_ctrl.clicks[2][1] == 2


def test_scroll_command_flow(command_registry, command_context):
    """Test scroll command with exponential scaling."""
    mouse_ctrl = command_context.mouse_controller

    # First scroll up - base amount (3)
    result, executed = command_registry.process("scroll up", command_context)
    assert executed
    assert len(mouse_ctrl.scrolls) == 1
    assert mouse_ctrl.scrolls[0] == (0, -3)

    # Second scroll up - doubled (6)
    result, executed = command_registry.process("scroll up", command_context)
    assert executed
    assert len(mouse_ctrl.scrolls) == 2
    assert mouse_ctrl.scrolls[1] == (0, -6)

    # Third scroll up - doubled again (12)
    result, executed = command_registry.process("scroll up", command_context)
    assert executed
    assert len(mouse_ctrl.scrolls) == 3
    assert mouse_ctrl.scrolls[2] == (0, -12)

    # Different direction - reset scaling
    result, executed = command_registry.process("scroll down", command_context)
    assert executed
    assert len(mouse_ctrl.scrolls) == 4
    assert mouse_ctrl.scrolls[3] == (0, 3)  # Back to base


def test_command_priority_ordering(command_registry, command_context):
    """Test that commands are executed in priority order."""
    # Higher priority commands should match first

    # "right click" (priority 200) should match before "click" (priority 150)
    result, executed = command_registry.process("right click", command_context)
    assert executed
    mouse_ctrl = command_context.mouse_controller
    assert mouse_ctrl.clicks[0][0] == mouse.Button.right  # Not left


def test_no_command_match(command_registry, command_context):
    """Test behavior when no command matches."""
    result, executed = command_registry.process("this is not a command", command_context)

    # No command should execute
    assert not executed
    assert result is None


def test_command_validation(command_context, event_bus):
    """Test command validation before execution."""

    class ValidatingCommand(Command):
        """Command that validates before execution."""

        def __init__(self, should_validate=True):
            self.should_validate = should_validate
            self.executed = False

        def matches(self, text: str) -> bool:
            return text.lower() == "validate me"

        def execute(self, context: CommandContext, text: str):
            self.executed = True
            return None

        def validate(self, context: CommandContext, text: str) -> bool:
            return self.should_validate

        @property
        def priority(self) -> int:
            return 100

        @property
        def description(self) -> str:
            return "Test validation"

        @property
        def examples(self) -> list[str]:
            return ["validate me"]

    # Test with successful validation
    registry = CommandRegistry(event_bus)
    cmd = ValidatingCommand(should_validate=True)
    registry.register(cmd)

    result, executed = registry.process("validate me", command_context)
    assert executed
    assert cmd.executed

    # Test with failed validation
    registry.clear()
    cmd = ValidatingCommand(should_validate=False)
    registry.register(cmd)

    result, executed = registry.process("validate me", command_context)
    assert not executed
    assert not cmd.executed


def test_command_with_result_text(command_context, event_bus):
    """Test command that returns text to type."""

    class TextReturningCommand(Command):
        """Command that returns text to type."""

        def matches(self, text: str) -> bool:
            return text.lower() == "insert hello"

        def execute(self, context: CommandContext, text: str):
            return "Hello, World!"

        @property
        def priority(self) -> int:
            return 100

        @property
        def description(self) -> str:
            return "Insert hello"

        @property
        def examples(self) -> list[str]:
            return ["insert hello"]

    registry = CommandRegistry(event_bus)
    registry.register(TextReturningCommand())

    result, executed = registry.process("insert hello", command_context)
    assert executed
    assert result == "Hello, World!"


def test_multiple_commands_same_priority(command_context, event_bus):
    """Test that first matching command executes when priorities are equal."""

    class Command1(Command):
        def matches(self, text: str) -> bool:
            return "test" in text.lower()

        def execute(self, context: CommandContext, text: str):
            return "command1"

        @property
        def priority(self) -> int:
            return 100

        @property
        def description(self) -> str:
            return "Command 1"

    class Command2(Command):
        def matches(self, text: str) -> bool:
            return "test" in text.lower()

        def execute(self, context: CommandContext, text: str):
            return "command2"

        @property
        def priority(self) -> int:
            return 100

        @property
        def description(self) -> str:
            return "Command 2"

    registry = CommandRegistry(event_bus)
    registry.register(Command1())
    registry.register(Command2())

    # First registered command should execute
    result, executed = registry.process("test", command_context)
    assert executed
    assert result == "command1"


def test_event_flow_during_command_execution(command_registry, command_context, event_bus):
    """Test that events are published throughout command execution."""
    events = []

    def capture_event(event):
        events.append(event)

    # Subscribe to all command-related events
    event_bus.subscribe(EventType.COMMAND_DETECTED, capture_event)
    event_bus.subscribe(EventType.COMMAND_EXECUTED, capture_event)

    # Execute command
    command_registry.process("enter", command_context)

    # Should have received both DETECTED and EXECUTED events
    assert len(events) >= 2
    event_types = [e.event_type for e in events]
    assert EventType.COMMAND_DETECTED in event_types
    assert EventType.COMMAND_EXECUTED in event_types
