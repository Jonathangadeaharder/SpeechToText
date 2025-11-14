# Breaking Changes

## Current Version: 2.0.0 (November 2025)

### Summary
**Good news: No breaking changes yet!**

Version 2.0.0 introduces the new modular architecture (`src/`) alongside the existing `dictation.py`. Everything is **backward compatible**.

## Breaking Changes by Version

### Version 2.0.0 (November 2025) - NO BREAKING CHANGES ✅

**Status:** Fully backward compatible

- ✅ dictation.py works exactly as before
- ✅ config.yaml format unchanged
- ✅ All features preserved
- ✅ No API changes
- ✅ No behavior changes

**What's New (Non-Breaking):**
- New modular architecture in `src/`
- 175 automated tests
- Command pattern for voice commands
- Event-driven architecture
- Better code organization

**Migration Required:** None

---

### Version 2.1.0 (December 2025) - SOFT DEPRECATION ⚠️

**Status:** Deprecation warnings added, but everything still works

#### Changes

1. **Deprecation Warning in dictation.py**
   ```python
   # When running dictation.py
   DeprecationWarning: dictation.py is deprecated and will be removed in v3.0.
   Please use 'python main.py' instead. See MIGRATION.md for details.
   ```

   **Breaking?** No - just a warning
   **Action Required:** None (but recommended to switch)

2. **main.py Entry Point Added**
   ```bash
   # New recommended way (same functionality)
   python main.py

   # Old way still works
   python dictation.py
   ```

   **Breaking?** No - old way still works
   **Action Required:** Switch to main.py (recommended)

3. **Documentation Updated**
   - README now recommends main.py
   - dictation.py marked as deprecated in docs

   **Breaking?** No - documentation only
   **Action Required:** None

**Migration Required:** None (recommended to switch to main.py)

---

### Version 2.5.0 (January 2026) - HARD DEPRECATION ⚠️⚠️

**Status:** Prominent warnings, dictation.py discouraged

#### Changes

1. **Prominent Warning on dictation.py Startup**
   ```
   ======================================================================
   ⚠️  WARNING: dictation.py is DEPRECATED!
   ======================================================================
   This file will be removed in version 3.0 (March 2026)
   Please switch to: python main.py
   See MIGRATION.md for the migration guide
   ======================================================================
   Press Enter to continue (or Ctrl+C to exit)...
   ```

   **Breaking?** No - but requires manual confirmation
   **Action Required:** Migrate to main.py before v3.0

2. **dictation.py Removed from Official Documentation**
   - Only main.py documented
   - MIGRATION.md provides migration guide

   **Breaking?** No - code still works
   **Action Required:** Read MIGRATION.md

**Migration Required:** Strongly recommended (required before v3.0)

---

### Version 3.0.0 (March 2026) - BREAKING CHANGES 🔴

**Status:** dictation.py removed

#### BREAKING CHANGE #1: Entry Point Changed

**Old:**
```bash
python dictation.py
```

**New:**
```bash
python main.py
# OR
python -m src
```

**Reason:** Monolithic file replaced with modular architecture
**Migration:** Update startup scripts to use main.py
**Workaround:** Use legacy tag (`git checkout tags/legacy-dictation.py`)

---

#### BREAKING CHANGE #2: Import Paths Changed (for programmatic use)

**Old:**
```python
from dictation import Config, TextProcessor, AudioFeedback
```

**New:**
```python
from src.core.config import Config
from src.transcription.text_processor import TextProcessor
from src.audio.feedback import AudioFeedback
```

**Reason:** Code reorganized into packages
**Migration:** Update import statements
**Workaround:** Copy dictation.py into your project

---

#### BREAKING CHANGE #3: VoiceCommandProcessor API Changed

**Old:**
```python
from dictation import VoiceCommandProcessor

processor = VoiceCommandProcessor(config)
result = processor.process_command("copy")
```

**New:**
```python
from src.commands.registry import CommandRegistry
from src.commands.base import CommandContext
from src.commands.handlers.keyboard_commands import CopyCommand

# Setup
registry = CommandRegistry()
registry.register(CopyCommand())

# Create context
context = CommandContext(
    config=config,
    keyboard_controller=keyboard.Controller(),
    mouse_controller=mouse.Controller(),
)

# Process command
result, executed = registry.process("copy", context)
```

**Reason:** Massive if-elif chain replaced with Command pattern
**Migration:** Use CommandRegistry instead of VoiceCommandProcessor
**Workaround:** Wrap old code in compatibility layer (see below)

**Compatibility Layer:**
```python
# Add this to maintain old API temporarily
class LegacyCommandProcessor:
    def __init__(self, config):
        from src.commands.registry import CommandRegistry
        self.registry = CommandRegistry()
        # Register all commands...

    def process_command(self, text: str):
        result, executed = self.registry.process(text, self.context)
        return result

# Use it
processor = LegacyCommandProcessor(config)
result = processor.process_command("copy")  # Old API works!
```

---

#### BREAKING CHANGE #4: DictationEngine Constructor Signature

**Old:**
```python
from dictation import DictationEngine

engine = DictationEngine(config)
engine.start_recording()
```

**New:**
```python
from src.core.engine import DictationEngine
from src.core.events import EventBus

event_bus = EventBus()  # Now required!
engine = DictationEngine(config, event_bus)
engine.start_recording()
```

**Reason:** Event-driven architecture requires event bus
**Migration:** Create EventBus instance and pass it
**Workaround:** Use default event bus

**Easy Migration:**
```python
from src.core.engine import DictationEngine
from src.core.events import EventBus

# Create event bus (you can subscribe to events if you want)
event_bus = EventBus()

# Create engine (new signature)
engine = DictationEngine(config, event_bus)

# Use exactly as before
engine.start_recording()
engine.stop_recording()
```

---

#### BREAKING CHANGE #5: TextProcessor.process() Return Type

**Old:**
```python
from dictation import TextProcessor

processor = TextProcessor(config)
text = processor.process("Hello period")  # Returns: "Hello."
```

**New:**
```python
from src.transcription.text_processor import TextProcessor

processor = TextProcessor(config)
result = processor.process("Hello period")
text, command = result  # Returns: ("Hello.", None)

# OR with tuple unpacking
text, command = processor.process("Hello period")
```

**Reason:** Need to distinguish between text and command words
**Migration:** Unpack tuple or use index [0]

**Quick Fix:**
```python
# Option 1: Unpack
text, command = processor.process("Hello period")

# Option 2: Get text only
text = processor.process("Hello period")[0]

# Option 3: Compatibility wrapper
class LegacyTextProcessor:
    def __init__(self, config):
        from src.transcription.text_processor import TextProcessor
        self.processor = TextProcessor(config)

    def process(self, text: str) -> str:
        result, _ = self.processor.process(text)
        return result  # Old behavior!

processor = LegacyTextProcessor(config)
text = processor.process("Hello period")  # Works like old code!
```

---

#### BREAKING CHANGE #6: NumberedOverlay Moved

**Old:**
```python
from dictation import NumberedOverlay

overlay = NumberedOverlay()
overlay.show_grid()
```

**New:**
```python
from src.overlays.grid_overlay import GridOverlay

overlay = GridOverlay()
overlay.show()
```

**Reason:** Overlay split into multiple classes (Grid, Element, Window, etc.)
**Migration:** Use specific overlay class
**Workaround:** Import from new location

**Migration:**
```python
# Old: Single class for all overlays
overlay = NumberedOverlay()
overlay.show_grid()
overlay.show_numbers()
overlay.show_windows()

# New: Separate classes for each overlay type
from src.overlays.grid_overlay import GridOverlay
from src.overlays.element_overlay import ElementOverlay
from src.overlays.window_overlay import WindowOverlay

grid_overlay = GridOverlay()
grid_overlay.show()

element_overlay = ElementOverlay()
element_overlay.show()

window_overlay = WindowOverlay()
window_overlay.show(windows_dict)
```

---

## Non-Breaking Changes (Enhancements)

These are **additions** that don't break existing code:

### Event System (New in 2.0)
```python
from src.core.events import EventBus, Event, EventType

# Subscribe to events
event_bus = EventBus()
event_bus.subscribe(EventType.COMMAND_EXECUTED, lambda e: print(e.data))

# Events are published automatically by commands
```

**Breaking?** No - completely optional
**Benefit:** Monitor and react to events in your code

### Command Priority System (New in 2.0)
```python
class MyCommand(Command):
    @property
    def priority(self) -> int:
        return 500  # Higher = checked first
```

**Breaking?** No - automatic
**Benefit:** Control which commands match first

### Fuzzy Matching (New in 2.0)
```python
from src.commands.parser import CommandParser

parser = CommandParser()
parser.is_fuzzy_match("clicks", "click")  # True!
```

**Breaking?** No - automatic improvement
**Benefit:** Better speech recognition tolerance

### Number Homophones (Enhanced in 2.0)
```python
# Now recognizes "to" → 2, "for" → 4, "ate" → 8
parser.extract_numbers("to left for right")  # [2, 4]
```

**Breaking?** No - more numbers recognized
**Benefit:** Speech recognition errors handled better

## Migration Strategy

### Immediate (v2.0 - v2.1)
1. ✅ Test that dictation.py still works
2. ✅ Try running main.py
3. ✅ Verify config.yaml works with both

### Before v2.5 (by January 2026)
1. ⚠️ Switch to main.py for daily use
2. ⚠️ Update documentation/scripts to use main.py
3. ⚠️ Port any custom commands to src/

### Before v3.0 (by March 2026 - REQUIRED)
1. 🔴 Migrate all usage to main.py
2. 🔴 Update import paths if programmatic use
3. 🔴 Test thoroughly with new API
4. 🔴 Remove references to dictation.py

## Compatibility Layers

### Full Backward Compatibility Wrapper

If you absolutely need the old API in v3.0+:

```python
# legacy_wrapper.py
"""
Provides backward compatibility with dictation.py API.
Use this as a temporary bridge while migrating to new API.
"""

from src.core.config import Config
from src.core.engine import DictationEngine
from src.core.events import EventBus
from src.transcription.text_processor import TextProcessor
from src.commands.registry import CommandRegistry
from src.commands.base import CommandContext

# Import all command classes
from src.commands.handlers.keyboard_commands import *
from src.commands.handlers.mouse_commands import *
from src.commands.handlers.window_commands import *

class LegacyDictationEngine:
    """Wrapper that provides old DictationEngine API."""

    def __init__(self, config):
        self.config = config
        self.event_bus = EventBus()
        self.engine = DictationEngine(config, self.event_bus)

    def start_recording(self):
        return self.engine.start_recording()

    def stop_recording(self):
        return self.engine.stop_recording()

    # ... add other methods as needed

# Use it
from legacy_wrapper import LegacyDictationEngine
engine = LegacyDictationEngine(config)  # Old API!
engine.start_recording()
```

### Automated Migration Script

Coming soon: `scripts/migrate_to_main.py`

```bash
# Check what needs to be changed
python scripts/migrate_to_main.py --check

# Automatically update code
python scripts/migrate_to_main.py --migrate

# Dry run (safe)
python scripts/migrate_to_main.py --dry-run
```

## Testing for Breaking Changes

### Test Your Code Against v3.0

```bash
# 1. Check out v3.0 branch (when available)
git checkout v3.0-beta

# 2. Try running your code
python your_script.py

# 3. Check for errors
# - ImportError: Update imports
# - AttributeError: API changed, check BREAKING_CHANGES.md
# - TypeError: Function signature changed

# 4. Fix issues or use compatibility wrapper
```

### Automated Compatibility Check

```bash
# Run compatibility checker
python scripts/check_compatibility.py

# Output:
# ✓ config.yaml: Compatible
# ✗ my_script.py: Uses deprecated imports from dictation
# ✗ startup.sh: Calls python dictation.py
# Recommendation: See MIGRATION.md sections 2.1, 3.4
```

## Support and Help

### Getting Migration Help

**GitHub Issues:**
- Tag: `migration`, `breaking-change`
- Include: Your code, error messages, version numbers

**Migration Assistance:**
- We'll help you migrate before v3.0
- File issue tagged `migration-help`
- Show what you're trying to do

**Emergency Support:**
- Critical blocker preventing migration?
- File issue tagged `migration-blocker`
- We'll work with you to resolve

## Rollback Plan

### If You Can't Migrate

**Option 1: Use Legacy Tag**
```bash
git checkout tags/legacy-dictation.py
python dictation.py
```

**Option 2: Fork**
```bash
git checkout v2.5.0
git checkout -b my-legacy-fork
# Maintain yourself
```

**Option 3: Vendor**
```bash
cp dictation.py my_project/legacy_dictation.py
# Include in your project
```

## Summary of Breaking Changes

| Change | Version | Impact | Migration Effort |
|--------|---------|--------|-----------------|
| Entry point (dictation.py → main.py) | 3.0 | High | Easy (5 min) |
| Import paths changed | 3.0 | Medium | Easy (10 min) |
| VoiceCommandProcessor → CommandRegistry | 3.0 | Medium | Medium (30 min) |
| DictationEngine signature | 3.0 | Low | Easy (5 min) |
| TextProcessor return type | 3.0 | Low | Easy (5 min) |
| NumberedOverlay split | 3.0 | Low | Medium (15 min) |

**Total Migration Time:** 1-2 hours for typical usage

## FAQ

### Q: Will config.yaml change?
**A:** No! 100% backward compatible.

### Q: Do I need to rewrite all my code?
**A:** No. Most changes are import paths. Functionality is identical.

### Q: What if I use dictation.py in production?
**A:** You have until March 2026 to migrate. That's 4 months notice.

### Q: Can I delay migration past v3.0?
**A:** Yes, but you'll need to maintain dictation.py yourself (fork or vendor).

### Q: Will you provide a migration script?
**A:** Yes! `scripts/migrate_to_main.py` will automate most changes.

### Q: What if the migration script fails?
**A:** File an issue. We'll help you manually migrate.

### Q: Is there a grace period after v3.0?
**A:** No. v3.0 removes dictation.py. Migrate before release.

---

*Last updated: 2025-11-12*
*Next breaking changes: March 2026 (v3.0)*
