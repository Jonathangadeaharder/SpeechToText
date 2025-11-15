"""Keyboard command implementations."""

from typing import Optional

from pynput import keyboard

from src.commands.base import Command, CommandContext, PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_NORMAL


class KeyPressCommand(Command):
    """
    Generic key press command.

    Handles pressing a single key or special key.
    """

    def __init__(
        self,
        trigger_words: list[str],
        key: keyboard.Key,
        description: str,
        priority: int = PRIORITY_NORMAL
    ):
        """
        Initialize key press command.

        Args:
            trigger_words: List of words that trigger this command
            key: The keyboard key to press
            description: Description for help text
            priority: Command priority (default PRIORITY_NORMAL)
        """
        self._trigger_words = [w.lower() for w in trigger_words]
        self._key = key
        self._description = description
        self._priority = priority

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean in self._trigger_words

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Press the key."""
        context.keyboard_controller.press(self._key)
        context.keyboard_controller.release(self._key)
        # Event is published by registry, no need to publish here
        return None  # No text to type

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def description(self) -> str:
        return self._description

    @property
    def examples(self) -> list[str]:
        return self._trigger_words


class EnterCommand(KeyPressCommand):
    """Press Enter key."""

    def __init__(self):
        super().__init__(
            trigger_words=["enter"],
            key=keyboard.Key.enter,
            description="Press Enter key",
            priority=PRIORITY_NORMAL,
        )


class TabCommand(KeyPressCommand):
    """Press Tab key."""

    def __init__(self):
        super().__init__(
            trigger_words=["tab"],
            key=keyboard.Key.tab,
            description="Press Tab key",
            priority=PRIORITY_NORMAL,
        )


class EscapeCommand(KeyPressCommand):
    """Press Escape key."""

    def __init__(self):
        super().__init__(
            trigger_words=["escape", "cancel"],
            key=keyboard.Key.esc,
            description="Press Escape key",
            priority=PRIORITY_NORMAL,
        )


class SpaceCommand(KeyPressCommand):
    """Press Space key."""

    def __init__(self):
        super().__init__(
            trigger_words=["space"],
            key=keyboard.Key.space,
            description="Press Space key",
            priority=PRIORITY_NORMAL,
        )


class BackspaceCommand(KeyPressCommand):
    """Press Backspace key (delete one character)."""

    def __init__(self):
        super().__init__(
            trigger_words=["delete", "backspace"],
            key=keyboard.Key.backspace,
            description="Delete one character (Backspace)",
            priority=PRIORITY_NORMAL,
        )


class DeleteWordCommand(Command):
    """Delete the previous word (Ctrl+Backspace)."""

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean == "delete word"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Delete previous word using Ctrl+Backspace."""
        # Press Ctrl+Backspace to delete previous word
        context.keyboard_controller.press(keyboard.Key.ctrl)
        context.keyboard_controller.press(keyboard.Key.backspace)
        context.keyboard_controller.release(keyboard.Key.backspace)
        context.keyboard_controller.release(keyboard.Key.ctrl)
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_HIGH  # Higher priority than single "delete"

    @property
    def description(self) -> str:
        return "Delete previous word (Ctrl+Backspace)"

    @property
    def examples(self) -> list[str]:
        return ["delete word"]


class DeleteLineCommand(Command):
    """Delete the current line."""

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean == "delete line"

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Delete current line using Home, Shift+End, Delete."""
        # Move to start of line
        context.keyboard_controller.press(keyboard.Key.home)
        context.keyboard_controller.release(keyboard.Key.home)

        # Select to end of line
        context.keyboard_controller.press(keyboard.Key.shift)
        context.keyboard_controller.press(keyboard.Key.end)
        context.keyboard_controller.release(keyboard.Key.end)
        context.keyboard_controller.release(keyboard.Key.shift)

        # Delete selection
        context.keyboard_controller.press(keyboard.Key.delete)
        context.keyboard_controller.release(keyboard.Key.delete)

        return None

    @property
    def priority(self) -> int:
        return PRIORITY_HIGH  # Higher priority than single "delete"

    @property
    def description(self) -> str:
        return "Delete current line"

    @property
    def examples(self) -> list[str]:
        return ["delete line"]


class ClipboardCommand(Command):
    """
    Clipboard operations (copy, cut, paste).

    Uses Ctrl+C, Ctrl+X, Ctrl+V shortcuts.
    """

    def __init__(self):
        self._operations = {
            "copy": ("c", "Copying"),
            "cut": ("x", "Cutting"),
            "paste": ("v", "Pasting"),
        }

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean in self._operations

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute clipboard operation."""
        text_clean = self.strip_punctuation(text)
        key_char, action = self._operations[text_clean]

        # Press Ctrl+[key]
        with context.keyboard_controller.pressed(keyboard.Key.ctrl):
            context.keyboard_controller.press(key_char)
            context.keyboard_controller.release(key_char)

        # Event is published by registry, no need to publish here
        return None

    @property
    def priority(self) -> int:
        return PRIORITY_MEDIUM  # Higher priority than generic key commands

    @property
    def description(self) -> str:
        return "Clipboard operations (copy, cut, paste)"

    @property
    def examples(self) -> list[str]:
        return ["copy", "cut", "paste"]


class KeyboardShortcutCommand(Command):
    """
    Generic keyboard shortcut command (Ctrl+Key).

    DRY: Consolidates all Ctrl+Key commands into a single reusable class.
    """

    def __init__(
        self,
        trigger_words: list[str],
        key: str,
        description: str,
        priority: int = PRIORITY_MEDIUM,
        modifier: keyboard.Key = keyboard.Key.ctrl
    ):
        """
        Initialize keyboard shortcut command.

        Args:
            trigger_words: List of words that trigger this command
            key: The key to press (character)
            description: Description for help text
            priority: Command priority (default 200)
            modifier: Modifier key to use (default Ctrl)
        """
        self._trigger_words = [w.lower() for w in trigger_words]
        self._key = key
        self._description = description
        self._priority = priority
        self._modifier = modifier

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)
        return text_clean in self._trigger_words

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute keyboard shortcut."""
        with context.keyboard_controller.pressed(self._modifier):
            context.keyboard_controller.press(self._key)
            context.keyboard_controller.release(self._key)

        # Event is published by registry, no need to publish here
        return None

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def description(self) -> str:
        return self._description

    @property
    def examples(self) -> list[str]:
        return self._trigger_words


class SelectAllCommand(KeyboardShortcutCommand):
    """Select all text (Ctrl+A)."""

    def __init__(self):
        super().__init__(
            trigger_words=["select all"],
            key="a",
            description="Select all text (Ctrl+A)",
            priority=PRIORITY_MEDIUM
        )


class UndoCommand(KeyboardShortcutCommand):
    """Undo last action (Ctrl+Z)."""

    def __init__(self):
        super().__init__(
            trigger_words=["undo"],
            key="z",
            description="Undo last action (Ctrl+Z)",
            priority=PRIORITY_MEDIUM
        )


class RedoCommand(KeyboardShortcutCommand):
    """Redo last undone action (Ctrl+Y)."""

    def __init__(self):
        super().__init__(
            trigger_words=["redo"],
            key="y",
            description="Redo last undone action (Ctrl+Y)",
            priority=PRIORITY_MEDIUM
        )


class SaveCommand(KeyboardShortcutCommand):
    """Save file (Ctrl+S)."""

    def __init__(self):
        super().__init__(
            trigger_words=["save"],
            key="s",
            description="Save file (Ctrl+S)",
            priority=PRIORITY_MEDIUM
        )


class TypeTextCommand(Command):
    """
    Type text with 'type' prefix stripped.

    When you say "type <text>", this command strips "type" and types just <text>.
    Has lower priority than TypeSymbolCommand so symbols are handled first.
    Handles transcription errors like "type?" or "type!" by checking if word starts with "type"
    """

    def matches(self, text: str) -> bool:
        # Strip punctuation for matching
        text_clean = self.strip_punctuation(text)
        # Match "type something" with space
        if text_clean.startswith("type "):
            return True
        return False

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Strip 'type' prefix and return text to be typed."""
        # Strip punctuation from the text
        text_clean = self.strip_punctuation(text)

        if text_clean.startswith("type "):
            # Remove "type " prefix
            result = text_clean[5:].strip()
            return result if result else None

        return text_clean if text_clean else None

    @property
    def priority(self) -> int:
        return PRIORITY_HIGH  # High priority - TYPE command should match before substring matches in other commands

    @property
    def description(self) -> str:
        return "Type text with 'type' prefix stripped"

    @property
    def examples(self) -> list[str]:
        return ["type hello world", "type investigate why"]


class TypeSymbolCommand(Command):
    """
    Type a symbol character.

    Handles symbols that might be difficult to speak naturally.
    """

    def __init__(self):
        """Initialize symbol mappings."""
        self._symbols = {
            "slash": "/",
            "backslash": "\\",
            "open": "(",
            "open paren": "(",
            "close": ")",
            "close paren": ")",
            "curly open": "{",
            "open curly": "{",
            "curly close": "}",
            "close curly": "}",
            "equal": "=",
            "equals": "=",
            "quotation": '"',
            "quote": '"',
            "tick": "'",
            "apostrophe": "'",
            "dollar": "$",
            "and": "&",
            "ampersand": "&",
            "array open": "[",
            "open bracket": "[",
            "array close": "]",
            "close bracket": "]",
            "question": "?",
            "exclamation": "!",
            "percent": "%",
            "star": "*",
            "asterisk": "*",
            "plus": "+",
            "minus": "-",
            "dash": "-",
            "dot": ".",
            "period": ".",
            "colon": ":",
            "semicolon": ";",
            "comma": ",",
            "hashtag": "#",
            "hash": "#",
            "pound": "#",
            "greater": ">",
            "greater than": ">",
            "smaller": "<",
            "less than": "<",
            "bar": "|",
            "pipe": "|",
            "elevate": "^",
            "caret": "^",
            "round": "~",
            "tilde": "~",
        }

    def matches(self, text: str) -> bool:
        text_clean = self.strip_punctuation(text)

        # Check if it's exactly a symbol name
        if text_clean in self._symbols:
            return True

        # Check if it's exactly "type <symbol_name>"
        if text_clean.startswith("type "):
            symbol_part = text_clean[5:].strip()
            # Only match if the part after "type " is exactly a valid symbol
            if symbol_part in self._symbols:
                return True

        return False

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Type the symbol."""
        text_clean = self.strip_punctuation(text)
        # Strip "type" prefix if present
        if text_clean.startswith("type "):
            text_clean = text_clean[5:].strip()
        symbol = self._symbols[text_clean]
        return symbol  # Return symbol to be typed

    @property
    def priority(self) -> int:
        return PRIORITY_NORMAL  # Same as basic key commands

    @property
    def description(self) -> str:
        return "Type symbol characters"

    @property
    def examples(self) -> list[str]:
        return ["slash", "open paren", "close paren", "equals", "quote", "comma"]
