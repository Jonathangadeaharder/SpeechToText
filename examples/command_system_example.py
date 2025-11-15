"""
Example demonstrating the refactored command system.

This shows how to use the new modular architecture with:
- Command pattern for extensible voice commands
- Event-driven architecture for decoupled communication
- Dependency injection via CommandContext
- Text processing with punctuation commands
"""

from pynput import keyboard, mouse

from src.commands.base import CommandContext
from src.commands.parser import CommandParser
from src.commands.registry import CommandRegistry
from src.commands.handlers.keyboard_commands import (
    BackspaceCommand,
    ClipboardCommand,
    EnterCommand,
    EscapeCommand,
    RedoCommand,
    SaveCommand,
    SelectAllCommand,
    SpaceCommand,
    TabCommand,
    TypeSymbolCommand,
    UndoCommand,
)
from src.commands.handlers.mouse_commands import (
    ClickCommand,
    ClickNumberCommand,
    DoubleClickCommand,
    MiddleClickCommand,
    MouseMoveCommand,
    RightClickCommand,
    ScrollCommand,
)
from src.core.config import Config
from src.core.events import EventType, get_event_bus
from src.transcription.text_processor import TextProcessor


def main():
    """Example usage of the command system."""

    # 1. Load configuration
    config = Config("config.yaml")
    print("✓ Configuration loaded")

    # 2. Set up event bus for pub-sub messaging
    event_bus = get_event_bus()

    # Subscribe to command events
    def on_command_executed(event):
        print(f"  📢 Event: Command executed - {event.data.get('command', 'Unknown')}")

    event_bus.subscribe(EventType.COMMAND_EXECUTED, on_command_executed)
    print("✓ Event bus configured")

    # 3. Create command parser for number extraction and fuzzy matching
    parser = CommandParser()
    print("✓ Command parser initialized")

    # 4. Create command context with dependencies
    context = CommandContext(
        config=config,
        keyboard_controller=keyboard.Controller(),
        mouse_controller=mouse.Controller(),
        event_bus=event_bus,
        screen_width=1920,
        screen_height=1080,
    )
    print("✓ Command context created")

    # 5. Create command registry
    registry = CommandRegistry(event_bus=event_bus)
    print("✓ Command registry initialized")

    # 6. Register keyboard commands
    print("\n📝 Registering keyboard commands...")
    keyboard_commands = [
        EnterCommand(),
        TabCommand(),
        EscapeCommand(),
        SpaceCommand(),
        BackspaceCommand(),
        ClipboardCommand(),
        SelectAllCommand(),
        UndoCommand(),
        RedoCommand(),
        SaveCommand(),
        TypeSymbolCommand(),
    ]
    for cmd in keyboard_commands:
        registry.register(cmd)
    print(f"  ✓ Registered {len(keyboard_commands)} keyboard commands")

    # 7. Register mouse commands
    print("\n🖱️  Registering mouse commands...")
    mouse_commands = [
        ClickCommand(),
        RightClickCommand(),
        DoubleClickCommand(),
        MiddleClickCommand(),
        ScrollCommand(),
        MouseMoveCommand(),
        ClickNumberCommand(parser),
    ]
    for cmd in mouse_commands:
        registry.register(cmd)
    print(f"  ✓ Registered {len(mouse_commands)} mouse commands")

    # 8. Create text processor for punctuation commands
    text_processor = TextProcessor(config)
    print("\n📄 Text processor initialized")

    # 9. Show registry statistics
    print(f"\n📊 Registry Statistics:")
    print(f"  Total commands: {registry.get_command_count()}")
    print(f"  Enabled commands: {registry.get_command_count(enabled_only=True)}")

    # 10. Example: Process some voice commands
    print("\n🎤 Processing example voice commands:")
    print("-" * 50)

    # Example 1: Simple click
    print("\n1️⃣  Voice input: 'click'")
    result, executed = registry.process("click", context)
    print(f"  Result: {'Command executed' if executed else 'No match'}")

    # Example 2: Text with punctuation
    print("\n2️⃣  Voice input: 'Hello period How are you question mark'")
    text, command = text_processor.process("Hello period How are you question mark")
    if text:
        print(f"  Processed text: '{text}'")

    # Example 3: Clipboard command
    print("\n3️⃣  Voice input: 'copy'")
    result, executed = registry.process("copy", context)
    print(f"  Result: {'Command executed' if executed else 'No match'}")

    # Example 4: Type symbol
    print("\n4️⃣  Voice input: 'slash'")
    result, executed = registry.process("slash", context)
    if result:
        print(f"  Symbol to type: '{result}'")

    # Example 5: Scroll with exponential scaling
    print("\n5️⃣  Voice input: 'scroll down' (repeated)")
    scroll_cmd = ScrollCommand()
    for i in range(3):
        result = scroll_cmd.execute(context, "scroll down")
        print(f"  Scroll #{i+1}: Multiplier = 2^{i}")

    # Example 6: Command word detection
    print("\n6️⃣  Voice input: 'delete that'")
    text, command = text_processor.process("delete that")
    if command:
        print(f"  Command detected: '{command}'")

    # 11. Display help text
    print("\n" + "=" * 50)
    print("📚 Available Commands Help:")
    print("=" * 50)
    print(registry.get_help_text())

    print("\n✅ Example completed successfully!")
    print("\n💡 Key Features Demonstrated:")
    print("  • Command Pattern - Extensible, testable commands")
    print("  • Event-Driven Architecture - Decoupled components")
    print("  • Dependency Injection - Clean dependencies via context")
    print("  • Text Processing - Punctuation & vocabulary handling")
    print("  • Priority Ordering - Commands checked by priority")
    print("  • Number Parsing - Homophones ('to'→2, 'for'→4)")
    print("  • Exponential Scaling - Smart repeated command handling")


if __name__ == "__main__":
    main()
