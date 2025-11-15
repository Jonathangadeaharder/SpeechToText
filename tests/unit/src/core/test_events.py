"""Unit tests for the Event system."""

import unittest

from src.core.events import Event, EventBus, EventType, get_event_bus, reset_event_bus


class TestEvent(unittest.TestCase):
    """Test cases for Event class."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(EventType.RECORDING_STARTED)
        self.assertEqual(event.event_type, EventType.RECORDING_STARTED)
        self.assertEqual(event.data, {})

    def test_event_with_data(self):
        """Test creating an event with data."""
        data = {"timestamp": 12345, "user": "test"}
        event = Event(EventType.TRANSCRIPTION_COMPLETED, data)
        self.assertEqual(event.event_type, EventType.TRANSCRIPTION_COMPLETED)
        self.assertEqual(event.data, data)

    def test_event_repr(self):
        """Test event string representation."""
        event = Event(EventType.COMMAND_DETECTED, {"command": "test"})
        repr_str = repr(event)
        self.assertIn("COMMAND_DETECTED", repr_str)
        self.assertIn("command", repr_str)


class TestEventBus(unittest.TestCase):
    """Test cases for EventBus class."""

    def setUp(self):
        """Set up test fixtures."""
        self.bus = EventBus()
        self.events_received = []

    def tearDown(self):
        """Clean up after tests."""
        self.bus.clear_all()

    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish."""
        def callback(event):
            self.events_received.append(event)

        self.bus.subscribe(EventType.RECORDING_STARTED, callback)
        event = Event(EventType.RECORDING_STARTED, {"test": "data"})
        self.bus.publish(event)

        self.assertEqual(len(self.events_received), 1)
        self.assertEqual(self.events_received[0].event_type, EventType.RECORDING_STARTED)
        self.assertEqual(self.events_received[0].data["test"], "data")

    def test_multiple_subscribers(self):
        """Test multiple subscribers to the same event."""
        received_1 = []
        received_2 = []

        def callback_1(event):
            received_1.append(event)

        def callback_2(event):
            received_2.append(event)

        self.bus.subscribe(EventType.TEXT_PROCESSED, callback_1)
        self.bus.subscribe(EventType.TEXT_PROCESSED, callback_2)

        event = Event(EventType.TEXT_PROCESSED)
        self.bus.publish(event)

        self.assertEqual(len(received_1), 1)
        self.assertEqual(len(received_2), 1)

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        def callback(event):
            self.events_received.append(event)

        self.bus.subscribe(EventType.COMMAND_EXECUTED, callback)
        self.bus.publish(Event(EventType.COMMAND_EXECUTED))
        self.assertEqual(len(self.events_received), 1)

        # Unsubscribe and publish again
        self.bus.unsubscribe(EventType.COMMAND_EXECUTED, callback)
        self.bus.publish(Event(EventType.COMMAND_EXECUTED))
        self.assertEqual(len(self.events_received), 1)  # Should still be 1

    def test_no_duplicate_subscribers(self):
        """Test that subscribing twice with same callback doesn't duplicate."""
        def callback(event):
            self.events_received.append(event)

        self.bus.subscribe(EventType.OVERLAY_SHOWN, callback)
        self.bus.subscribe(EventType.OVERLAY_SHOWN, callback)  # Subscribe again

        self.bus.publish(Event(EventType.OVERLAY_SHOWN))
        self.assertEqual(len(self.events_received), 1)  # Should only be called once

    def test_different_event_types(self):
        """Test that subscribers only receive their subscribed event types."""
        def callback(event):
            self.events_received.append(event)

        self.bus.subscribe(EventType.RECORDING_STARTED, callback)

        # Publish different event type
        self.bus.publish(Event(EventType.RECORDING_STOPPED))
        self.assertEqual(len(self.events_received), 0)

        # Publish subscribed event type
        self.bus.publish(Event(EventType.RECORDING_STARTED))
        self.assertEqual(len(self.events_received), 1)

    def test_error_handling(self):
        """Test that errors in one callback don't affect others."""
        def failing_callback(event):
            raise Exception("Test error")

        def working_callback(event):
            self.events_received.append(event)

        self.bus.subscribe(EventType.ERROR_OCCURRED, failing_callback)
        self.bus.subscribe(EventType.ERROR_OCCURRED, working_callback)

        # Publish event - working callback should still be called
        self.bus.publish(Event(EventType.ERROR_OCCURRED))
        self.assertEqual(len(self.events_received), 1)

    def test_get_subscriber_count(self):
        """Test getting subscriber count for an event type."""
        self.assertEqual(self.bus.get_subscriber_count(EventType.CONFIG_CHANGED), 0)

        def callback_1(event):
            pass

        def callback_2(event):
            pass

        self.bus.subscribe(EventType.CONFIG_CHANGED, callback_1)
        self.assertEqual(self.bus.get_subscriber_count(EventType.CONFIG_CHANGED), 1)

        self.bus.subscribe(EventType.CONFIG_CHANGED, callback_2)
        self.assertEqual(self.bus.get_subscriber_count(EventType.CONFIG_CHANGED), 2)

    def test_clear_all(self):
        """Test clearing all subscribers."""
        def callback(event):
            self.events_received.append(event)

        self.bus.subscribe(EventType.NOTIFICATION_SHOWN, callback)
        self.bus.subscribe(EventType.TRANSCRIPTION_STARTED, callback)

        self.bus.clear_all()
        self.assertEqual(self.bus.get_subscriber_count(EventType.NOTIFICATION_SHOWN), 0)
        self.assertEqual(self.bus.get_subscriber_count(EventType.TRANSCRIPTION_STARTED), 0)


class TestGlobalEventBus(unittest.TestCase):
    """Test cases for global event bus singleton."""

    def tearDown(self):
        """Clean up after tests."""
        reset_event_bus()

    def test_get_event_bus_singleton(self):
        """Test that get_event_bus returns the same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        self.assertIs(bus1, bus2)

    def test_reset_event_bus(self):
        """Test resetting the global event bus."""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()
        self.assertIsNot(bus1, bus2)


if __name__ == '__main__':
    unittest.main()
