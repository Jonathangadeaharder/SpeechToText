# Architecture Documentation

## Overview

This document describes the refactored architecture of the Speech-to-Text Dictation Tool. The system has been redesigned from a monolithic 3,420-line file into a modular, maintainable architecture following SOLID principles.

## Project Structure

```
SpeechToText/
├── src/                    # Source code (NEW modular architecture)
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management ✓ COMPLETE
│   │   └── events.py      # Event system (TODO)
│   │
│   ├── audio/             # Audio processing
│   │   ├── feedback.py    # Audio feedback/beeps ✓ COMPLETE
│   │   ├── vad.py         # Voice Activity Detection ✓ COMPLETE
│   │   └── capture.py     # Audio capture (TODO)
│   │
│   ├── transcription/     # Speech-to-text
│   │   ├── whisper_transcriber.py  # (TODO)
│   │   └── text_processor.py       # (TODO)
│   │
│   ├── commands/          # Command system
│   │   ├── base.py        # Command interface (TODO)
│   │   ├── registry.py    # Command registry (TODO)
│   │   ├── parser.py      # Command parsing (TODO)
│   │   ├── handlers/      # Command implementations (TODO)
│   │   └── matchers/      # Fuzzy matching (TODO)
│   │
│   ├── input/             # Input control
│   │   ├── keyboard_controller.py  # (TODO)
│   │   ├── mouse_controller.py     # (TODO)
│   │   └── text_injector.py        # (TODO)
│   │
│   ├── window_manager/    # Window management
│   │   ├── base.py        # Abstract interface (TODO)
│   │   └── windows_manager.py  # Windows impl (TODO)
│   │
│   ├── overlays/          # UI overlays
│   │   ├── base.py        # Overlay interface (TODO)
│   │   ├── grid_overlay.py     # (TODO)
│   │   ├── element_overlay.py  # (TODO)
│   │   └── ...
│   │
│   ├── ui/                # User interface
│   │   └── system_tray.py # (TODO)
│   │
│   └── utils/             # Utilities
│       └── timing.py      # Performance timing (TODO)
│
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   │   └── test_config.py  # ✓ COMPLETE
│   └── integration/       # Integration tests
│
├── config/                # Configuration files
│   ├── config.yaml
│   └── number_mappings.yaml
│
└── dictation.py           # LEGACY monolithic file (for reference)
```

## Design Patterns Used

### 1. Command Pattern
Replaces the massive if-elif chain with pluggable command objects.

**Benefits:**
- Easy to add new commands
- Each command is independently testable
- Command priority system
- Validation before execution

### 2. Strategy Pattern
Separate overlay implementations instead of mode-switching in one class.

**Benefits:**
- Single Responsibility Principle
- Easy to add new overlay types
- Clear separation of concerns

### 3. Dependency Injection
Components receive dependencies through constructors instead of creating them.

**Benefits:**
- Testability (can mock dependencies)
- Loose coupling
- Clear dependencies

### 4. Event-Driven Architecture
Components communicate through events instead of direct coupling.

**Benefits:**
- Decoupled components
- Easy to add observers
- Extensible system

### 5. Registry Pattern
Central registry for commands instead of hard-coded checks.

**Benefits:**
- Dynamic registration
- Plugin architecture
- No code modification for new commands

## Migration Status

### Phase 1: Extract Core Infrastructure ✅ COMPLETE

- [x] Create package structure
- [x] Extract Config class
- [x] Extract AudioFeedback class
- [x] Extract VoiceActivityDetector class
- [x] Set up test infrastructure
- [x] Extract TextProcessor class ✓ COMPLETE (96% test coverage, 12/12 tests passing)
- [x] Create Event system ✓ COMPLETE (100% test coverage, 13/13 tests passing)

### Phase 2: Refactor Command System ✅ IN PROGRESS

- [x] Create Command base class and interface ✓ COMPLETE (97% test coverage, 18/18 tests passing)
- [x] Implement CommandRegistry ✓ COMPLETE (86% test coverage, 24/24 tests passing)
- [x] Create CommandParser with fuzzy matching ✓ COMPLETE (95% test coverage, 42/42 tests passing)
- [x] Port keyboard commands ✓ COMPLETE (89% test coverage, 36/36 tests passing)
- [x] Port mouse commands ✓ COMPLETE (87% test coverage, 26/26 tests passing)
- [ ] Port window management commands
- [ ] Port navigation commands
- [ ] Port overlay commands

### Phase 3: Refactor Overlay System ⏳ TODO

- [ ] Create Overlay base class
- [ ] Implement OverlayManager
- [ ] Create GridOverlay
- [ ] Create ElementOverlay (Windows UI Automation)
- [ ] Create WindowListOverlay
- [ ] Create RowOverlay
- [ ] Create HelpOverlay

### Phase 4: Complete Migration ⏳ TODO

- [ ] Extract DictationEngine refactoring
- [ ] Create main.py entry point
- [ ] Integration testing
- [ ] Performance benchmarking
- [ ] Documentation
- [ ] Deprecate old dictation.py

## Architecture Principles

### Single Responsibility Principle (SRP)
Each class/module has one reason to change.

**Example:** AudioFeedback only handles beep generation, not audio capture or transcription.

### Open/Closed Principle (OCP)
Open for extension, closed for modification.

**Example:** New commands can be added without modifying CommandRegistry.

### Dependency Inversion Principle (DIP)
Depend on abstractions, not concretions.

**Example:** DictationEngine depends on Transcriber interface, not WhisperModel directly.

## Testing Strategy

### Unit Tests
- Test individual classes in isolation
- Mock dependencies
- Fast execution
- High code coverage target: >80%

### Integration Tests
- Test component interactions
- Real dependencies where feasible
- End-to-end command flows

### Performance Tests
- Benchmark transcription speed
- Measure command processing latency
- Track memory usage

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run unit tests only
python -m pytest tests/unit/

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test
python -m pytest tests/unit/test_config.py
```

## Code Quality Metrics

### Target Metrics
- Lines per file: < 300
- Lines per class: < 200
- Methods per class: < 20
- Lines per method: < 30
- Cyclomatic complexity: < 10
- Test coverage: > 80%

### Current Status (New Code)
- ✅ Config: 127 lines
- ✅ AudioFeedback: 62 lines
- ✅ VoiceActivityDetector: 77 lines

## Development Guidelines

### Adding a New Command

1. Create command class inheriting from `Command`
2. Implement `matches()` and `execute()` methods
3. Set appropriate priority
4. Write unit tests
5. Register in command setup

Example:
```python
class MyCommand(Command):
    def matches(self, text: str) -> bool:
        return text.lower() == "my command"

    def execute(self, context: CommandContext) -> None:
        # Execute command logic
        return None

    @property
    def priority(self) -> int:
        return 100
```

### Adding a New Overlay

1. Create overlay class inheriting from `Overlay`
2. Implement `show()`, `hide()`, and `handle_input()`
3. Register with OverlayManager
4. Write unit tests

## Performance Considerations

### Optimization Points
1. **Window list caching** - Cache window enumeration for 5 seconds
2. **Lazy loading** - Load overlays only when needed
3. **Thread pool** - Parallelize independent operations
4. **Number parsing caching** - Cache parsed number mappings

### Monitoring
- Timing breakdown for each phase
- Memory profiling for large overlays
- Thread count monitoring

## Future Enhancements

### Planned Features
- [ ] Plugin system for third-party commands
- [ ] Command macros/scripting
- [ ] Multi-language support
- [ ] Cloud synchronization for configs
- [ ] Command history and analytics

### Technical Debt
- Remove pywinauto dependency for cross-platform support
- Migrate to modern async/await for audio processing
- Consider replacing tkinter overlays with native platform APIs

## References

- Original monolithic file: `dictation.py` (3,420 lines)
- Config: `config.yaml`
- Number mappings: `number_mappings.yaml`

## Contributors

Architecture redesign: 2025-11-12

---

*Last updated: 2025-11-12*
