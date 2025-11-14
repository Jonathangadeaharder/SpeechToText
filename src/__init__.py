"""
Speech-to-Text Dictation Tool - Modular Architecture

This package contains the refactored, modular implementation of the
dictation tool, organized by responsibility following SOLID principles.

Main modules:
- core: Configuration, events, and core infrastructure
- audio: Audio capture, feedback, and voice activity detection
- transcription: Speech-to-text processing
- commands: Voice command system (Command pattern)
- input: Keyboard and mouse control
- window_manager: Window management (platform-specific)
- overlays: UI overlays for visual feedback
- ui: User interface components
- utils: Shared utilities
"""

__version__ = "2.0.0"
__all__ = []
