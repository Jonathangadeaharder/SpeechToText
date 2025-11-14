# Deprecation Plan for dictation.py

## Executive Summary

`dictation.py` is the original monolithic implementation (3,528 lines). It will be **gradually deprecated** in favor of the new modular architecture in `src/`. This document outlines the deprecation timeline and migration path.

## Current Status

| Item | Status | Support Level |
|------|--------|--------------|
| dictation.py | ✅ Active | Full support |
| src/ (new code) | ✅ Active | Partial functionality |
| main.py | ⏳ Not yet created | N/A |

## Deprecation Timeline

### Phase 0: Current State (November 2025)
**Status:** Both old and new code coexist

- ✅ dictation.py is the **primary entry point**
- ✅ src/ contains refactored components
- ✅ 175 tests passing for new code
- ✅ Zero breaking changes

**User Action Required:** None

### Phase 1: Soft Deprecation (December 2025)
**Status:** main.py released, dictation.py still works

- ✅ main.py becomes **primary entry point**
- ✅ dictation.py still fully functional
- ⚠️ Add deprecation warning to dictation.py
- ✅ Update README to recommend main.py

**Deprecation Warning Added:**
```python
# At top of dictation.py
import warnings
warnings.warn(
    "dictation.py is deprecated and will be removed in v3.0. "
    "Please use 'python main.py' instead. "
    "See MIGRATION.md for details.",
    DeprecationWarning,
    stacklevel=2
)
```

**User Action Required:**
- Recommended: Switch to `python main.py`
- Optional: Continue using `python dictation.py` (still works)

### Phase 2: Hard Deprecation (January 2026)
**Status:** dictation.py discouraged but works

- ⚠️ dictation.py shows **prominent warning**
- ✅ main.py feature-complete
- ✅ All features migrated
- ✅ Integration tests passing
- ⚠️ dictation.py removed from documentation

**Warning Updated:**
```python
print("=" * 70)
print("⚠️  WARNING: dictation.py is DEPRECATED!")
print("=" * 70)
print("This file will be removed in version 3.0 (March 2026)")
print("Please switch to: python main.py")
print("See MIGRATION.md for the migration guide")
print("=" * 70)
input("Press Enter to continue (or Ctrl+C to exit)...")
```

**User Action Required:**
- **Strongly recommended:** Migrate to main.py
- If stuck: File an issue explaining why
- Continuing with dictation.py: Must acknowledge warning

### Phase 3: Removal (March 2026)
**Status:** dictation.py removed from main branch

- ❌ dictation.py **removed** from repository
- ✅ Available in git history (tag: `legacy-dictation.py`)
- ✅ Archived as `legacy/dictation.py.backup`
- ✅ main.py is only entry point

**User Action Required:**
- **Required:** Migrate to main.py
- If still using dictation.py: Check out legacy tag

## What's Being Deprecated

### Components in dictation.py

| Component | Lines | New Location | Migration Difficulty |
|-----------|-------|--------------|---------------------|
| Config | 105 | src/core/config.py | ✅ Easy (API identical) |
| AudioFeedback | 38 | src/audio/feedback.py | ✅ Easy |
| NumberedOverlay | 870 | src/overlays/*.py | ⚠️ Medium (split into multiple classes) |
| VoiceCommandProcessor | 1,640 | src/commands/handlers/*.py | ⚠️ Medium (now command classes) |
| TextProcessor | 80 | src/transcription/text_processor.py | ✅ Easy |
| VoiceActivityDetector | 54 | src/audio/vad.py | ✅ Easy |
| DictationEngine | 457 | src/core/engine.py | 🔴 Hard (core refactor) |
| SystemTrayIcon | 46 | src/ui/system_tray.py | ✅ Easy |
| CodeChangeHandler | 30 | src/utils/watcher.py | ✅ Easy |
| main() | 70 | main.py | ✅ Easy |

## Migration Paths

### For End Users

#### Option 1: Automatic Migration (Recommended)
```bash
# After main.py is released (Phase 1)
python main.py  # Just works!
```

Your `config.yaml` is **100% compatible**. No changes needed.

#### Option 2: Stick with dictation.py (Temporary)
```bash
# Will work until Phase 3 (March 2026)
python dictation.py
```

You'll see warnings but it will work. Use this if:
- You're not ready to migrate yet
- You found a bug in main.py
- You need time to test

#### Option 3: Use Legacy Branch (Last Resort)
```bash
# After Phase 3, if you really can't migrate
git checkout tags/legacy-dictation.py
python dictation.py
```

**Not recommended.** You won't get:
- Bug fixes
- New features
- Security updates

### For Developers/Contributors

#### Option 1: Work on src/ (Recommended)
```python
# Import from new modules
from src.core.config import Config
from src.commands.registry import CommandRegistry
from src.commands.handlers.keyboard_commands import EnterCommand

# Create your feature using new architecture
config = Config()
registry = CommandRegistry()
registry.register(EnterCommand())
```

#### Option 2: Fix dictation.py (Short-term)
If you find a critical bug in dictation.py before Phase 3:
1. Fix it in dictation.py
2. **Also** port the fix to src/
3. Add a test to prevent regression

#### Option 3: Extend Both (Bridge Period)
During Phases 1-2, you might need to:
1. Add feature to src/
2. Optionally backport to dictation.py
3. Mark backport with `# TODO: Remove in v3.0`

## Breaking Changes

### Phase 0 → Phase 1 (No Breaking Changes)
✅ **Fully backward compatible**
- dictation.py still works
- config.yaml unchanged
- All features work

### Phase 1 → Phase 2 (No Breaking Changes)
✅ **Fully backward compatible**
- dictation.py still works (with warnings)
- config.yaml unchanged

### Phase 2 → Phase 3 (BREAKING CHANGES)
🔴 **Breaking changes introduced**

#### 1. Entry Point Change
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

#### 2. Import Path Changes (if you imported from dictation.py)
**Old:**
```python
from dictation import Config, TextProcessor
```

**New:**
```python
from src.core.config import Config
from src.transcription.text_processor import TextProcessor
```

#### 3. Class API Changes (minor)

**VoiceCommandProcessor** split into multiple commands:
```python
# Old (monolithic)
processor = VoiceCommandProcessor(config)
result = processor.process_command("copy")

# New (command pattern)
from src.commands.registry import CommandRegistry
from src.commands.handlers.keyboard_commands import CopyCommand

registry = CommandRegistry()
registry.register(CopyCommand())
result, executed = registry.process("copy", context)
```

**DictationEngine** API slightly different:
```python
# Old
engine = DictationEngine(config)
engine.start_recording()

# New (same, but with more events)
from src.core.engine import DictationEngine
from src.core.events import EventBus

event_bus = EventBus()
engine = DictationEngine(config, event_bus)
engine.start_recording()  # Now publishes events!
```

## Support Policy

### Phase 0-1: Full Support (Nov 2025 - Jan 2026)
- ✅ Bug fixes for dictation.py
- ✅ New features in src/
- ✅ Security updates for both
- ✅ Documentation for both

### Phase 2: Maintenance Only (Jan 2026 - Mar 2026)
- ✅ Critical bug fixes only for dictation.py
- ✅ New features only in src/
- ✅ Security updates for both
- ⚠️ Documentation focused on src/

### Phase 3+: No Support (Mar 2026+)
- ❌ No updates to dictation.py
- ✅ All development on src/
- ✅ Security updates only for src/
- ❌ No documentation for dictation.py

## Migration Assistance

### Automated Migration Tool (Coming Soon)
```bash
# Will analyze your usage and suggest changes
python scripts/migrate_to_main.py --check

# Will automatically update your code
python scripts/migrate_to_main.py --migrate

# Dry run (safe)
python scripts/migrate_to_main.py --dry-run
```

### Migration Checklist

**Before Phase 3 (by March 2026), ensure:**

- [ ] You can run `python main.py` successfully
- [ ] Your config.yaml works with main.py
- [ ] All your custom commands are ported (if any)
- [ ] You're not importing from dictation.py directly
- [ ] Your startup scripts use main.py, not dictation.py
- [ ] You've tested all features you use

### Getting Help

**Community Support:**
- GitHub Issues: Report problems
- GitHub Discussions: Ask questions
- Pull Requests: Contribute fixes

**Migration Issues:**
- Tag with `migration`
- Include error messages
- Show old vs new code
- Explain what you're trying to achieve

## Rollback Plan

### If main.py Has Critical Bugs

**Phase 1-2:** Easy rollback
```bash
# Just use dictation.py instead
python dictation.py
```

**Phase 3+:** Use legacy tag
```bash
git checkout tags/legacy-dictation.py
python dictation.py
```

### Emergency Support

If you can't migrate by Phase 3 due to a blocking issue:
1. File a GitHub issue **before March 2026**
2. Tag it `migration-blocker`
3. Explain why you can't migrate
4. We'll work with you to resolve it

## Legacy Support Options

### Option 1: Fork (DIY)
If you really need dictation.py long-term:
```bash
git checkout tags/legacy-dictation.py
git checkout -b my-legacy-branch
# Maintain yourself
```

### Option 2: Vendor (Copy)
Copy dictation.py into your own project:
```bash
cp dictation.py my_project/legacy_dictation.py
# Maintain as needed
```

### Option 3: Container (Freeze)
Use a Docker container with old version:
```dockerfile
FROM python:3.10
COPY dictation.py /app/
# Frozen in time
```

## Frequently Asked Questions

### Q: Why deprecate dictation.py?
**A:** 3,528 lines in one file is unmaintainable. The new architecture is:
- Easier to understand (modules < 400 lines)
- Easier to test (175 tests, 92% coverage)
- Easier to extend (add commands without modifying core)
- Better organized (SOLID principles)

### Q: Will main.py have feature parity?
**A:** Yes, 100%. All features from dictation.py will work in main.py.

### Q: What if I've modified dictation.py?
**A:** Options:
1. Port your changes to src/ (recommended)
2. Keep using your modified dictation.py (fork it)
3. Contribute your changes to src/ via PR

### Q: Can I delay migration past Phase 3?
**A:** Yes, but:
- No support after March 2026
- No bug fixes
- No security updates
- You're on your own

### Q: What if my config.yaml doesn't work?
**A:** File an issue immediately. We guarantee config.yaml compatibility.

### Q: Will there be a grace period?
**A:** Yes! Phases 1-2 provide 3 months overlap where both work.

## Recommendations

### For Casual Users
- **Phase 1:** Switch to main.py when released
- **Phase 2:** Must switch before March 2026
- **Phase 3:** Using main.py happily

### For Power Users
- **Phase 0:** Start exploring src/ now
- **Phase 1:** Test main.py thoroughly
- **Phase 2:** Migrate custom code
- **Phase 3:** Fully on main.py

### For Developers
- **Phase 0:** Contribute to src/, not dictation.py
- **Phase 1:** Port features from dictation.py
- **Phase 2:** Help others migrate
- **Phase 3:** Build new features on src/

## Conclusion

dictation.py served us well, but it's time to move to a more maintainable architecture. The deprecation will be:

- ✅ **Gradual** (5 months notice)
- ✅ **Well-communicated** (warnings, docs, support)
- ✅ **Backward compatible** (config.yaml unchanged)
- ✅ **Fully supported** (migration assistance available)

**Timeline Summary:**
- Nov 2025: Both work, use either
- Dec 2025: main.py released, switch recommended
- Jan 2026: dictation.py deprecated, switch strongly recommended
- Mar 2026: dictation.py removed, must use main.py

---

*Last updated: 2025-11-12*
*Deprecation start: December 2025 (Phase 1)*
*Removal date: March 2026 (Phase 3)*
