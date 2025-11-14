"""Unit tests for the CommandRegistry class."""

import os
import tempfile
import unittest
from unittest.mock import Mock

import yaml
from pynput import keyboard, mouse

from src.commands.base import Command, CommandContext, CommandExecutionError
from src.commands.registry import CommandRegistry
from src.core.config import Config
from src.core.events import Event, EventBus, EventType


class MockCommand(Command):
    """Mock command for testing."""

    def __init__(self, match_text="test", priority_val=100, should_fail=False):
        self.match_text = match_text
        self.priority_val = priority_val
        self.should_fail = should_fail
        self.executed = False
        self.execution_count = 0

    def matches(self, text: str) -> bool:
        return text.lower() == self.match_text.lower()

    def execute(self, context: CommandContext, text: str) -> str:
        if self.should_fail:
            raise CommandExecutionError(self.__class__.__name__, "Mock failure")
        self.executed = True
        self.execution_count += 1
        return f"Result: {text}"

    @property
    def priority(self) -> int:
        return self.priority_val

    @property
    def description(self) -> str:
        return f"Mock command matching '{self.match_text}'"

    @property
    def examples(self) -> list[str]:
        return [self.match_text, f"{self.match_text} example"]


class DisabledCommand(Command):
    """Command that is disabled."""

    def matches(self, text: str) -> bool:
        return text.lower() == "disabled"

    def execute(self, context: CommandContext, text: str) -> str:
        return "Should not execute"

    @property
    def priority(self) -> int:
        return 100

    @property
    def description(self) -> str:
        return "Disabled command"

    @property
    def enabled(self) -> bool:
        return False


class FailingValidationCommand(Command):
    """Command that fails validation."""

    def matches(self, text: str) -> bool:
        return text.lower() == "invalid"

    def execute(self, context: CommandContext, text: str) -> str:
        return "Should not execute"

    def validate(self, context: CommandContext, text: str) -> bool:
        return False

    @property
    def priority(self) -> int:
        return 100

    @property
    def description(self) -> str:
        return "Command with failing validation"


class TestCommandRegistry(unittest.TestCase):
    """Test cases for CommandRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal config
        self.config_data = {
            "advanced": {
                "log_level": "INFO",
            }
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config_data, self.temp_file)
        self.temp_file.close()

        self.config = Config(self.temp_file.name)
        self.context = CommandContext(
            config=self.config,
            keyboard_controller=keyboard.Controller(),
            mouse_controller=mouse.Controller(),
        )
        self.event_bus = EventBus()
        self.registry = CommandRegistry(event_bus=self.event_bus)

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.temp_file.name)

    def test_registry_creation(self):
        """Test creating a command registry."""
        registry = CommandRegistry()
        self.assertIsNotNone(registry)
        self.assertEqual(registry.get_command_count(), 0)

    def test_registry_with_event_bus(self):
        """Test registry with event bus."""
        self.assertEqual(self.registry.event_bus, self.event_bus)

    def test_register_command(self):
        """Test registering a command."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)
        self.assertEqual(self.registry.get_command_count(), 1)

    def test_register_multiple_commands(self):
        """Test registering multiple commands."""
        cmd1 = MockCommand("hello", priority_val=100)
        cmd2 = MockCommand("world", priority_val=200)
        cmd3 = MockCommand("test", priority_val=150)

        self.registry.register(cmd1)
        self.registry.register(cmd2)
        self.registry.register(cmd3)

        self.assertEqual(self.registry.get_command_count(), 3)

    def test_commands_sorted_by_priority(self):
        """Test that commands are sorted by priority (highest first)."""
        cmd1 = MockCommand("low", priority_val=100)
        cmd2 = MockCommand("high", priority_val=500)
        cmd3 = MockCommand("medium", priority_val=250)

        self.registry.register(cmd1)
        self.registry.register(cmd2)
        self.registry.register(cmd3)

        commands = self.registry.get_commands()
        self.assertEqual(commands[0].priority, 500)  # high priority first
        self.assertEqual(commands[1].priority, 250)
        self.assertEqual(commands[2].priority, 100)

    def test_unregister_command(self):
        """Test unregistering a command."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)
        self.assertEqual(self.registry.get_command_count(), 1)

        result = self.registry.unregister(cmd)
        self.assertTrue(result)
        self.assertEqual(self.registry.get_command_count(), 0)

    def test_unregister_nonexistent_command(self):
        """Test unregistering a command that was never registered."""
        cmd = MockCommand("hello")
        result = self.registry.unregister(cmd)
        self.assertFalse(result)

    def test_clear_commands(self):
        """Test clearing all commands."""
        self.registry.register(MockCommand("cmd1"))
        self.registry.register(MockCommand("cmd2"))
        self.registry.register(MockCommand("cmd3"))
        self.assertEqual(self.registry.get_command_count(), 3)

        self.registry.clear()
        self.assertEqual(self.registry.get_command_count(), 0)

    def test_get_commands_enabled_only(self):
        """Test getting only enabled commands."""
        enabled_cmd = MockCommand("enabled")
        disabled_cmd = DisabledCommand()

        self.registry.register(enabled_cmd)
        self.registry.register(disabled_cmd)

        all_commands = self.registry.get_commands(enabled_only=False)
        self.assertEqual(len(all_commands), 2)

        enabled_commands = self.registry.get_commands(enabled_only=True)
        self.assertEqual(len(enabled_commands), 1)
        self.assertEqual(enabled_commands[0], enabled_cmd)

    def test_find_matching_command(self):
        """Test finding a matching command."""
        cmd1 = MockCommand("hello", priority_val=100)
        cmd2 = MockCommand("world", priority_val=200)

        self.registry.register(cmd1)
        self.registry.register(cmd2)

        matched = self.registry.find_matching_command("hello")
        self.assertEqual(matched, cmd1)

        matched = self.registry.find_matching_command("world")
        self.assertEqual(matched, cmd2)

    def test_find_matching_command_priority_order(self):
        """Test that higher priority commands are matched first."""
        # Both commands match "test" but different priorities
        cmd1 = MockCommand("test", priority_val=100)
        cmd2 = MockCommand("test", priority_val=500)  # Higher priority

        self.registry.register(cmd1)
        self.registry.register(cmd2)

        # Should match cmd2 (higher priority)
        matched = self.registry.find_matching_command("test")
        self.assertEqual(matched, cmd2)

    def test_find_matching_command_no_match(self):
        """Test finding command when no match exists."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)

        matched = self.registry.find_matching_command("goodbye")
        self.assertIsNone(matched)

    def test_find_matching_command_ignores_disabled(self):
        """Test that disabled commands are not matched by default."""
        disabled_cmd = DisabledCommand()
        self.registry.register(disabled_cmd)

        # Should not match disabled command
        matched = self.registry.find_matching_command("disabled", enabled_only=True)
        self.assertIsNone(matched)

        # Should match when including disabled
        matched = self.registry.find_matching_command("disabled", enabled_only=False)
        self.assertEqual(matched, disabled_cmd)

    def test_process_successful_command(self):
        """Test processing text with successful command execution."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)

        result, executed = self.registry.process("hello", self.context)
        self.assertTrue(executed)
        self.assertEqual(result, "Result: hello")
        self.assertTrue(cmd.executed)
        self.assertEqual(cmd.execution_count, 1)

    def test_process_no_matching_command(self):
        """Test processing text with no matching command."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)

        result, executed = self.registry.process("goodbye", self.context)
        self.assertFalse(executed)
        self.assertIsNone(result)
        self.assertFalse(cmd.executed)

    def test_process_disabled_command(self):
        """Test processing disabled command."""
        disabled_cmd = DisabledCommand()
        self.registry.register(disabled_cmd)

        result, executed = self.registry.process("disabled", self.context, enabled_only=True)
        self.assertFalse(executed)
        self.assertIsNone(result)

    def test_process_failing_validation(self):
        """Test processing command that fails validation."""
        cmd = FailingValidationCommand()
        self.registry.register(cmd)

        result, executed = self.registry.process("invalid", self.context)
        self.assertFalse(executed)
        self.assertIsNone(result)

    def test_process_failing_execution(self):
        """Test processing command that fails during execution."""
        cmd = MockCommand("fail", should_fail=True)
        self.registry.register(cmd)

        with self.assertRaises(CommandExecutionError):
            self.registry.process("fail", self.context)

    def test_process_publishes_command_detected_event(self):
        """Test that processing publishes COMMAND_DETECTED event."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe(EventType.COMMAND_DETECTED, callback)

        self.registry.process("hello", self.context)

        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].event_type, EventType.COMMAND_DETECTED)
        self.assertEqual(events_received[0].data["text"], "hello")
        self.assertEqual(events_received[0].data["command_class"], "MockCommand")

    def test_process_publishes_command_executed_event(self):
        """Test that processing publishes COMMAND_EXECUTED event."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe(EventType.COMMAND_EXECUTED, callback)

        self.registry.process("hello", self.context)

        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].event_type, EventType.COMMAND_EXECUTED)
        self.assertEqual(events_received[0].data["text"], "hello")
        self.assertEqual(events_received[0].data["result"], "Result: hello")

    def test_process_publishes_command_failed_event_on_validation_failure(self):
        """Test that processing publishes COMMAND_FAILED event on validation failure."""
        cmd = FailingValidationCommand()
        self.registry.register(cmd)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe(EventType.COMMAND_FAILED, callback)

        self.registry.process("invalid", self.context)

        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].event_type, EventType.COMMAND_FAILED)
        self.assertEqual(events_received[0].data["reason"], "validation_failed")

    def test_get_help_text(self):
        """Test generating help text."""
        cmd1 = MockCommand("hello", priority_val=100)
        cmd2 = MockCommand("world", priority_val=200)

        self.registry.register(cmd1)
        self.registry.register(cmd2)

        help_text = self.registry.get_help_text()
        self.assertIn("Available Commands:", help_text)
        self.assertIn("Mock command matching 'hello'", help_text)
        self.assertIn("Mock command matching 'world'", help_text)
        self.assertIn("Priority: 100", help_text)
        self.assertIn("Priority: 200", help_text)

    def test_get_help_text_empty_registry(self):
        """Test generating help text for empty registry."""
        help_text = self.registry.get_help_text()
        self.assertEqual(help_text, "No commands registered.")

    def test_get_help_text_with_examples(self):
        """Test that help text includes examples."""
        cmd = MockCommand("hello")
        self.registry.register(cmd)

        help_text = self.registry.get_help_text()
        self.assertIn("Examples:", help_text)
        self.assertIn('"hello"', help_text)
        self.assertIn('"hello example"', help_text)

    def test_find_matching_command_with_exception_in_matches(self):
        """Test that find_matching_command handles exceptions in matches()."""
        class BrokenMatchCommand(Command):
            def matches(self, text: str) -> bool:
                raise Exception("Test error in matches()")

            def execute(self, context: CommandContext, text: str) -> str:
                return "Should not execute"

            @property
            def priority(self) -> int:
                return 100

            @property
            def description(self) -> str:
                return "Broken match command"

        broken_cmd = BrokenMatchCommand()
        self.registry.register(broken_cmd)

        # Should not crash, should return None
        result = self.registry.find_matching_command("test")
        self.assertIsNone(result)

    def test_process_with_exception_in_validate(self):
        """Test that process handles exceptions during validation."""
        class ExceptionValidationCommand(Command):
            def matches(self, text: str) -> bool:
                return text.lower() == "error"

            def validate(self, context: CommandContext, text: str) -> bool:
                raise Exception("Test validation error")

            def execute(self, context: CommandContext, text: str) -> str:
                return "Should not execute"

            @property
            def priority(self) -> int:
                return 100

            @property
            def description(self) -> str:
                return "Exception validation command"

        cmd = ExceptionValidationCommand()
        self.registry.register(cmd)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe(EventType.COMMAND_FAILED, callback)

        result, executed = self.registry.process("error", self.context)

        # Should handle exception gracefully
        self.assertIsNone(result)
        self.assertFalse(executed)

        # Should publish COMMAND_FAILED event
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].data["reason"], "validation_error")
        self.assertIn("Test validation error", events_received[0].data["error"])

    def test_process_with_unexpected_exception_in_execute(self):
        """Test that process handles unexpected exceptions during execution."""
        class UnexpectedErrorCommand(Command):
            def matches(self, text: str) -> bool:
                return text.lower() == "crash"

            def execute(self, context: CommandContext, text: str) -> str:
                raise RuntimeError("Unexpected test error")

            @property
            def priority(self) -> int:
                return 100

            @property
            def description(self) -> str:
                return "Unexpected error command"

        cmd = UnexpectedErrorCommand()
        self.registry.register(cmd)

        events_received = []

        def callback(event):
            events_received.append(event)

        self.event_bus.subscribe(EventType.COMMAND_FAILED, callback)

        # Should raise CommandExecutionError
        with self.assertRaises(CommandExecutionError):
            self.registry.process("crash", self.context)

        # Should publish COMMAND_FAILED event
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].data["reason"], "unexpected_error")
        self.assertIn("Unexpected test error", events_received[0].data["error"])


if __name__ == '__main__':
    unittest.main()
