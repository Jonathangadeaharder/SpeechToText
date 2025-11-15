"""
Integration tests for event propagation through the system.

Tests that events flow correctly between components and that
subscribers receive events in the expected order.
"""

import pytest
import time

from src.commands.base import Command, CommandContext
from src.commands.registry import CommandRegistry
from src.core.config import Config
from src.core.events import Event, EventBus, EventType


class MockKeyboardController:
    """Mock keyboard controller."""

    def press(self, key):
        pass

    def release(self, key):
        pass

    def pressed(self, key):
        class PressedContext:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return PressedContext()


class SimpleTestCommand(Command):
    """Simple test command that publishes events."""

    def __init__(self, event_bus):
        self.event_bus = event_bus

    def matches(self, text: str) -> bool:
        return text.lower() == "test"

    def execute(self, context: CommandContext, text: str):
        # Publish custom event during execution
        if self.event_bus:
            self.event_bus.publish(
                Event(EventType.TEXT_PROCESSED, {"message": "command executed"})
            )
        return None

    @property
    def priority(self) -> int:
        return 100

    @property
    def description(self) -> str:
        return "Test command"

    @property
    def examples(self) -> list[str]:
        return ["test"]


@pytest.fixture
def config():
    """Create test configuration."""
    config = Config()
    config.config = {"advanced": {"log_level": "DEBUG"}}
    return config


@pytest.fixture
def event_bus():
    """Create event bus."""
    return EventBus()


@pytest.fixture
def command_context(config, event_bus):
    """Create command context."""
    return CommandContext(
        config=config,
        keyboard_controller=MockKeyboardController(),
        mouse_controller=None,
        event_bus=event_bus,
    )


def test_event_publishing_and_receiving(event_bus):
    """Test basic event publish/subscribe functionality."""
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe
    event_bus.subscribe(EventType.COMMAND_EXECUTED, handler)

    # Publish event
    event = Event(EventType.COMMAND_EXECUTED, {"test": "data"})
    event_bus.publish(event)

    # Verify received
    assert len(received_events) == 1
    assert received_events[0].event_type == EventType.COMMAND_EXECUTED
    assert received_events[0].data["test"] == "data"


def test_multiple_subscribers_same_event(event_bus):
    """Test that multiple subscribers receive the same event."""
    received_1 = []
    received_2 = []
    received_3 = []

    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: received_1.append(e))
    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: received_2.append(e))
    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: received_3.append(e))

    # Publish event
    event = Event(EventType.RECORDING_STARTED, {"timestamp": time.time()})
    event_bus.publish(event)

    # All subscribers should receive
    assert len(received_1) == 1
    assert len(received_2) == 1
    assert len(received_3) == 1


def test_different_event_types_isolation(event_bus):
    """Test that subscribers only receive events they subscribed to."""
    recording_events = []
    transcription_events = []
    command_events = []

    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: recording_events.append(e))
    event_bus.subscribe(EventType.TRANSCRIPTION_COMPLETED, lambda e: transcription_events.append(e))
    event_bus.subscribe(EventType.COMMAND_EXECUTED, lambda e: command_events.append(e))

    # Publish different event types
    event_bus.publish(Event(EventType.RECORDING_STARTED, {}))
    event_bus.publish(Event(EventType.TRANSCRIPTION_COMPLETED, {}))
    event_bus.publish(Event(EventType.COMMAND_EXECUTED, {}))

    # Each subscriber should only receive their event type
    assert len(recording_events) == 1
    assert len(transcription_events) == 1
    assert len(command_events) == 1


def test_command_execution_event_flow(event_bus, command_context):
    """Test event flow during command execution."""
    events = []

    def capture_all(event):
        events.append(event)

    # Subscribe to all command-related events
    event_bus.subscribe(EventType.COMMAND_DETECTED, capture_all)
    event_bus.subscribe(EventType.COMMAND_EXECUTED, capture_all)
    event_bus.subscribe(EventType.COMMAND_FAILED, capture_all)

    # Create registry and register command
    registry = CommandRegistry(event_bus)
    registry.register(SimpleTestCommand(event_bus))

    # Execute command
    registry.process("test", command_context)

    # Should have received DETECTED and EXECUTED events
    event_types = [e.event_type for e in events]
    assert EventType.COMMAND_DETECTED in event_types
    assert EventType.COMMAND_EXECUTED in event_types

    # Events should be in order: DETECTED -> EXECUTED
    detected_idx = event_types.index(EventType.COMMAND_DETECTED)
    executed_idx = event_types.index(EventType.COMMAND_EXECUTED)
    assert detected_idx < executed_idx


def test_command_failure_event(event_bus, command_context):
    """Test that COMMAND_FAILED event is published on validation failure."""

    class FailingCommand(Command):
        def matches(self, text: str) -> bool:
            return text.lower() == "fail"

        def validate(self, context: CommandContext, text: str) -> bool:
            return False  # Always fail validation

        def execute(self, context: CommandContext, text: str):
            return None

        @property
        def priority(self) -> int:
            return 100

        @property
        def description(self) -> str:
            return "Failing command"

        @property
        def examples(self) -> list[str]:
            return ["fail"]

    events = []
    event_bus.subscribe(EventType.COMMAND_FAILED, lambda e: events.append(e))

    registry = CommandRegistry(event_bus)
    registry.register(FailingCommand())

    # Try to execute (should fail validation)
    result, executed = registry.process("fail", command_context)

    # Should not execute
    assert not executed

    # Should publish COMMAND_FAILED event
    assert len(events) == 1
    assert events[0].event_type == EventType.COMMAND_FAILED
    assert events[0].data["reason"] == "validation_failed"


def test_unsubscribe_functionality(event_bus):
    """Test unsubscribing from events."""
    received = []

    def handler(event):
        received.append(event)

    # Subscribe
    event_bus.subscribe(EventType.RECORDING_STARTED, handler)

    # Publish - should receive
    event_bus.publish(Event(EventType.RECORDING_STARTED, {}))
    assert len(received) == 1

    # Unsubscribe
    event_bus.unsubscribe(EventType.RECORDING_STARTED, handler)

    # Publish again - should not receive
    event_bus.publish(Event(EventType.RECORDING_STARTED, {}))
    assert len(received) == 1  # Still just 1


def test_event_data_payload(event_bus):
    """Test that event data payloads are correctly transmitted."""
    received_events = []

    event_bus.subscribe(EventType.TRANSCRIPTION_COMPLETED, lambda e: received_events.append(e))

    # Publish event with complex data
    event_data = {
        "text": "Hello world",
        "language": "en",
        "language_probability": 0.99,
        "duration": 1.5,
        "timestamp": time.time(),
    }

    event_bus.publish(Event(EventType.TRANSCRIPTION_COMPLETED, event_data))

    # Verify data is intact
    assert len(received_events) == 1
    received_data = received_events[0].data
    assert received_data["text"] == "Hello world"
    assert received_data["language"] == "en"
    assert received_data["language_probability"] == 0.99
    assert received_data["duration"] == 1.5
    assert "timestamp" in received_data


def test_error_event_publishing(event_bus):
    """Test ERROR_OCCURRED event handling."""
    errors = []

    event_bus.subscribe(EventType.ERROR_OCCURRED, lambda e: errors.append(e))

    # Publish error event
    event_bus.publish(
        Event(
            EventType.ERROR_OCCURRED,
            {"component": "test_component", "error": "Something went wrong", "severity": "critical"},
        )
    )

    assert len(errors) == 1
    assert errors[0].data["component"] == "test_component"
    assert errors[0].data["error"] == "Something went wrong"


def test_event_ordering_guarantee(event_bus):
    """Test that events are received in the order they are published."""
    events = []

    def handler(event):
        events.append(event)

    event_bus.subscribe(EventType.TEXT_PROCESSED, handler)

    # Publish multiple events in sequence
    for i in range(10):
        event_bus.publish(Event(EventType.TEXT_PROCESSED, {"order": i}))

    # Verify order
    assert len(events) == 10
    for i, event in enumerate(events):
        assert event.data["order"] == i


def test_subscriber_error_isolation(event_bus):
    """Test that an error in one subscriber doesn't affect others."""
    received_1 = []
    received_2 = []

    def failing_handler(event):
        raise Exception("Handler error")

    def good_handler(event):
        received_1.append(event)

    def another_good_handler(event):
        received_2.append(event)

    # Subscribe handlers (one will fail)
    event_bus.subscribe(EventType.COMMAND_EXECUTED, good_handler)
    event_bus.subscribe(EventType.COMMAND_EXECUTED, failing_handler)
    event_bus.subscribe(EventType.COMMAND_EXECUTED, another_good_handler)

    # Publish event
    event_bus.publish(Event(EventType.COMMAND_EXECUTED, {}))

    # Good handlers should still receive the event despite the failing handler
    assert len(received_1) == 1
    assert len(received_2) == 1


def test_event_bus_clear_all(event_bus):
    """Test clearing all subscribers."""
    received = []

    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: received.append(e))
    event_bus.subscribe(EventType.RECORDING_STOPPED, lambda e: received.append(e))

    # Clear all subscribers
    event_bus.clear_all()

    # Publish events - should not be received
    event_bus.publish(Event(EventType.RECORDING_STARTED, {}))
    event_bus.publish(Event(EventType.RECORDING_STOPPED, {}))

    assert len(received) == 0


def test_event_bus_get_subscriber_count(event_bus):
    """Test getting subscriber count for event types."""
    # Initially no subscribers
    assert event_bus.get_subscriber_count(EventType.RECORDING_STARTED) == 0

    # Add subscribers
    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: None)
    assert event_bus.get_subscriber_count(EventType.RECORDING_STARTED) == 1

    event_bus.subscribe(EventType.RECORDING_STARTED, lambda e: None)
    assert event_bus.get_subscriber_count(EventType.RECORDING_STARTED) == 2

    # Different event type should still be 0
    assert event_bus.get_subscriber_count(EventType.RECORDING_STOPPED) == 0


def test_complex_event_flow_scenario(event_bus, command_context):
    """Test a complex scenario with multiple event types and subscribers."""
    # Simulate a complete dictation flow with event tracking
    event_log = []

    def log_event(event):
        event_log.append((event.event_type, event.data.get("stage", "unknown")))

    # Subscribe to all event types
    for event_type in [
        EventType.RECORDING_STARTED,
        EventType.RECORDING_STOPPED,
        EventType.TRANSCRIPTION_STARTED,
        EventType.TRANSCRIPTION_COMPLETED,
        EventType.TEXT_PROCESSED,
        EventType.COMMAND_DETECTED,
        EventType.COMMAND_EXECUTED,
        EventType.TEXT_TYPED,
    ]:
        event_bus.subscribe(event_type, log_event)

    # Simulate dictation flow
    event_bus.publish(Event(EventType.RECORDING_STARTED, {"stage": "1"}))
    event_bus.publish(Event(EventType.RECORDING_STOPPED, {"stage": "2"}))
    event_bus.publish(Event(EventType.TRANSCRIPTION_STARTED, {"stage": "3"}))
    event_bus.publish(Event(EventType.TRANSCRIPTION_COMPLETED, {"stage": "4"}))
    event_bus.publish(Event(EventType.TEXT_PROCESSED, {"stage": "5"}))
    event_bus.publish(Event(EventType.COMMAND_DETECTED, {"stage": "6"}))
    event_bus.publish(Event(EventType.COMMAND_EXECUTED, {"stage": "7"}))
    event_bus.publish(Event(EventType.TEXT_TYPED, {"stage": "8"}))

    # Verify all events were received in order
    assert len(event_log) == 8
    for i, (event_type, stage) in enumerate(event_log):
        assert stage == str(i + 1)
