"""Event system for decoupled component communication."""

import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
from enum import Enum, auto

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of all event types in the application."""

    # Audio events
    RECORDING_STARTED = auto()
    RECORDING_STOPPED = auto()
    AUDIO_CHUNK_RECEIVED = auto()

    # Transcription events
    TRANSCRIPTION_STARTED = auto()
    TRANSCRIPTION_COMPLETED = auto()
    TRANSCRIPTION_FAILED = auto()

    # Command events
    COMMAND_DETECTED = auto()
    COMMAND_EXECUTED = auto()
    COMMAND_FAILED = auto()

    # Text processing events
    TEXT_PROCESSED = auto()
    TEXT_TYPED = auto()

    # UI events
    OVERLAY_SHOWN = auto()
    OVERLAY_HIDDEN = auto()
    NOTIFICATION_SHOWN = auto()

    # System events
    ERROR_OCCURRED = auto()
    CONFIG_CHANGED = auto()


class Event:
    """
    Represents an event with a type and optional data payload.

    Attributes:
        event_type: Type of the event
        data: Optional dictionary containing event-specific data
    """

    def __init__(self, event_type: EventType, data: Optional[Dict[str, Any]] = None):
        """
        Initialize an event.

        Args:
            event_type: The type of event
            data: Optional data payload for the event
        """
        self.event_type = event_type
        self.data = data or {}

    def __repr__(self) -> str:
        return f"Event({self.event_type.name}, {self.data})"


class EventBus:
    """
    Central event bus for publish-subscribe messaging between components.

    Allows components to communicate without direct dependencies by publishing
    and subscribing to events.

    Example:
        ```python
        bus = EventBus()

        # Subscribe to an event
        def on_recording_started(event):
            logger.info(f"Recording started: {event.data}")

        bus.subscribe(EventType.RECORDING_STARTED, on_recording_started)

        # Publish an event
        bus.publish(Event(EventType.RECORDING_STARTED, {"timestamp": time.time()}))
        ```
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is published (receives Event object)
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: The event to publish
        """
        for callback in self._subscribers[event.event_type]:
            try:
                callback(event)
            except Exception as e:
                # Log the error but don't stop other callbacks
                logger.error(f"Error in event callback for {event.event_type.name}: {e}")

    def clear_all(self) -> None:
        """Clear all subscribers (useful for testing)."""
        self._subscribers.clear()

    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: The event type to check

        Returns:
            Number of subscribers
        """
        return len(self._subscribers[event_type])


# Global event bus instance (singleton pattern)
_global_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance (singleton).

    Returns:
        The global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _global_event_bus
    _global_event_bus = None
