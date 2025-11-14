"""Custom user-defined commands from config.yaml."""

import logging
import os
import subprocess
import time
from typing import Any, Optional

try:
    import pyperclip
except ImportError:
    pyperclip = None

from src.commands.base import Command, CommandContext, PRIORITY_HIGH


class CustomCommand(Command):
    """
    Custom command defined by user in config.yaml.

    Supports four action types:
    - type_text: Types specified text
    - copy_to_clipboard: Copies text to clipboard
    - execute_file: Runs a file/program
    - key_combination: Presses key combinations
    """

    def __init__(self, trigger: str, action_type: str, action_data: dict):
        """
        Initialize custom command.

        Args:
            trigger: Trigger phrase (e.g., "admin user")
            action_type: Type of action (type_text, execute_file, key_combination)
            action_data: Action parameters (text, path, keys, etc.)
        """
        self.logger = logging.getLogger(f"CustomCommand:{trigger}")
        self.trigger = trigger.lower().strip()
        self.action_type = action_type
        self.action_data = action_data

    def matches(self, text: str) -> bool:
        """Check if text matches this custom command."""
        text_clean = self.strip_punctuation(text)
        return text_clean == self.trigger

    def execute(self, context: CommandContext, text: str) -> Optional[str]:
        """Execute the custom command."""
        try:
            if self.action_type == "type_text":
                return self._execute_type_text(context)
            elif self.action_type == "copy_to_clipboard":
                return self._execute_copy_to_clipboard(context)
            elif self.action_type == "execute_file":
                return self._execute_file(context)
            elif self.action_type == "key_combination":
                return self._execute_key_combination(context)
            else:
                self.logger.error(f"Unknown action type: {self.action_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error executing custom command: {e}")
            return None

    def _execute_type_text(self, context: CommandContext) -> Optional[str]:
        """Execute type_text action."""
        text = self.action_data.get("text", "")
        if not text:
            self.logger.warning("No text specified for type_text action")
            return None

        # Type the text using keyboard controller
        context.keyboard_controller.type(text)
        return None  # Text was typed, don't return it

    def _execute_copy_to_clipboard(self, context: CommandContext) -> Optional[str]:
        """Execute copy_to_clipboard action."""
        text = self.action_data.get("text", "")
        if not text:
            self.logger.warning("No text specified for copy_to_clipboard action")
            return None

        # Copy to clipboard using PowerShell (cross-platform alternative)
        try:
            if os.name == 'nt':  # Windows
                # Use PowerShell to set clipboard
                subprocess.run(
                    ['powershell', '-Command', f'Set-Clipboard -Value "{text}"'],
                    check=True,
                    capture_output=True
                )
                self.logger.info(f"Copied to clipboard: {text}")
            elif pyperclip:
                # Use pyperclip for cross-platform support
                pyperclip.copy(text)
                self.logger.info(f"Copied to clipboard: {text}")
            else:
                self.logger.error("Clipboard not supported on this platform")
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")

        return None

    def _execute_file(self, context: CommandContext) -> Optional[str]:
        """Execute execute_file action."""
        path = self.action_data.get("path", "")
        if not path:
            self.logger.warning("No path specified for execute_file action")
            return None

        # Expand environment variables
        path = os.path.expandvars(path)

        # Check if file exists
        if not os.path.exists(path):
            self.logger.error(f"File not found: {path}")
            return None

        # Execute the file
        try:
            # Run without waiting (non-blocking)
            subprocess.Popen(
                path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.logger.info(f"Executed: {path}")
        except Exception as e:
            self.logger.error(f"Error executing file: {e}")

        return None

    def _execute_key_combination(self, context: CommandContext) -> Optional[str]:
        """Execute key_combination action."""
        keys = self.action_data.get("keys", [])
        if not keys:
            self.logger.warning("No keys specified for key_combination action")
            return None

        # Press all keys in the combination
        try:
            # Press all keys down
            for key in keys:
                context.keyboard_controller.press(key)

            # Small delay
            time.sleep(0.05)

            # Release all keys in reverse order
            for key in reversed(keys):
                context.keyboard_controller.release(key)

        except Exception as e:
            self.logger.error(f"Error executing key combination: {e}")

        return None

    @property
    def priority(self) -> int:
        """Custom commands have high priority to override built-in commands."""
        return PRIORITY_HIGH

    @property
    def description(self) -> str:
        """Get command description."""
        if self.action_type == "type_text":
            text = self.action_data.get("text", "")
            # Truncate long text
            if len(text) > 30:
                text = text[:27] + "..."
            return f"Type: {text}"
        elif self.action_type == "copy_to_clipboard":
            text = self.action_data.get("text", "")
            # Truncate long text
            if len(text) > 30:
                text = text[:27] + "..."
            return f"Copy: {text}"
        elif self.action_type == "execute_file":
            path = self.action_data.get("path", "")
            filename = os.path.basename(path)
            return f"Run: {filename}"
        elif self.action_type == "key_combination":
            keys = self.action_data.get("keys", [])
            keys_str = "+".join(keys)
            return f"Press: {keys_str}"
        return "Custom command"

    @property
    def examples(self) -> list[str]:
        """Get example usage."""
        return [self.trigger]


def load_custom_commands(config: Any) -> list[CustomCommand]:
    """
    Load custom commands from config.

    Args:
        config: Config object with custom_commands section

    Returns:
        List of CustomCommand instances
    """
    logger = logging.getLogger("CustomCommands")
    commands = []

    try:
        # Check if custom commands are enabled
        enabled = config.get("custom_commands", "enabled", default=False)
        print(f"[DEBUG] Custom commands enabled: {enabled}")
        if not enabled:
            logger.info("Custom commands disabled in config")
            print("[DEBUG] Custom commands disabled in config")
            return commands

        # Get command list
        custom_cmds = config.get("custom_commands", "commands", default=[])
        print(f"[DEBUG] Found {len(custom_cmds) if custom_cmds else 0} custom command definitions")
        if not custom_cmds:
            logger.info("No custom commands defined in config")
            print("[DEBUG] No custom commands defined in config")
            return commands

        # Create command instances
        for i, cmd_config in enumerate(custom_cmds):
            try:
                trigger = cmd_config.get("trigger")
                action = cmd_config.get("action", {})
                action_type = action.get("type")

                print(f"[DEBUG] Command {i+1}: trigger='{trigger}', type='{action_type}'")

                if not trigger or not action_type:
                    logger.warning(f"Invalid custom command config: {cmd_config}")
                    print(f"[DEBUG] Invalid command config (missing trigger or type)")
                    continue

                # Create command
                cmd = CustomCommand(trigger, action_type, action)
                commands.append(cmd)
                logger.info(f"Loaded custom command: '{trigger}' -> {action_type}")
                print(f"[DEBUG] ✓ Successfully loaded: '{trigger}' -> {action_type}")

            except Exception as e:
                logger.error(f"Error loading custom command: {e}")
                print(f"[DEBUG] ✗ Error loading command: {e}")
                continue

        logger.info(f"Loaded {len(commands)} custom commands")
        print(f"[DEBUG] Total custom commands loaded: {len(commands)}")

    except Exception as e:
        logger.error(f"Error loading custom commands from config: {e}")

    return commands
