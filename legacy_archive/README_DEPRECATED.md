# Legacy Code Archive

This directory contains deprecated code that has been replaced by the new modular architecture.

## ⚠️ DEPRECATED FILES

### dictation.py.DEPRECATED (3,528 lines)
**Status:** Removed as of v3.0 (Nov 2025)
**Replaced by:** `src/main.py` and modular architecture in `src/`

This was the original monolithic implementation. All functionality has been migrated to the new architecture with:
- Better separation of concerns
- 443 comprehensive tests
- 92%+ code coverage
- SOLID principles throughout
- Extensible command system
- Modular overlay system

**Do not use this file.** It is kept only for historical reference.

### benchmark_models.py.OLD
**Status:** Archived
**Reason:** Superseded by new performance testing approach

Old benchmarking script that compared different Whisper model implementations.

## Migration Information

If you were using the old `dictation.py`:

### Use the new system instead:
```bash
# Primary entry point
python run.py

# Or directly
python src/main.py
```

### Your config.yaml works unchanged
No configuration changes needed - 100% backward compatible.

### Getting Help
- See `../MIGRATION.md` for detailed migration guide
- See `../ARCHITECTURE.md` for new architecture overview
- See `../COMPLETE_MIGRATION_SUMMARY.md` for full details
- See `../RELEASE_NOTES_v3.0.md` for v3.0 changes

## Timeline

- **Nov 2025 (Phase 0):** Both old and new code coexisted
- **Dec 2025 (Phase 1):** Soft deprecation warnings added
- **Jan 2026 (Phase 2):** Hard deprecation requiring confirmation
- **Mar 2026 (Phase 3):** Old code removed ✅ **YOU ARE HERE**

## Why Was This Deprecated?

The monolithic `dictation.py` had several issues:
- **3,528 lines** in a single file
- **100+ cyclomatic complexity** (hard to understand/modify)
- **No tests** (0% coverage)
- **Tight coupling** between components
- **Difficult to extend** with new features
- **Hard to debug** due to global state

The new architecture solves all these issues:
- **40+ modular files** averaging 200 lines each
- **Low complexity** (<10 per function)
- **443 tests** with 92% coverage
- **Loose coupling** via dependency injection
- **Easy to extend** via command pattern
- **Easy to debug** with clear boundaries

## Restoration (Emergency Only)

If you absolutely need to restore the old code temporarily:

```bash
# Copy from archive (NOT RECOMMENDED)
cp legacy_archive/dictation.py.DEPRECATED dictation.py

# Then run
python dictation.py
```

**Warning:** The old code is no longer maintained. Use at your own risk. Security updates, bug fixes, and new features will only be added to the new system.

## Questions?

See the main documentation in the root directory or open an issue on GitHub.
