#!/usr/bin/env python3
"""
Startup script for the Speech-to-Text Dictation Tool.

This script provides:
- Dependency checking
- Helpful error messages
- Progress indication
- Graceful error handling
"""

import sys
from pathlib import Path

# Colors for terminal output (ANSI escape codes)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def check_python_version():
    """Check Python version."""
    print_header("Checking Python version...")

    if sys.version_info < (3, 8):
        print_error(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        print(f"\nPlease upgrade Python: https://www.python.org/downloads/")
        return False

    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_config_file():
    """Check if config.yaml exists."""
    print_header("Checking configuration file...")

    config_path = Path("config.yaml")
    if not config_path.exists():
        print_error("config.yaml not found!")
        print("\nThe configuration file is required to run the dictation tool.")
        print("Expected location: ./config.yaml")
        return False

    print_success(f"Found config.yaml ({config_path.stat().st_size} bytes)")
    return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    print_header("Checking dependencies...")

    required_packages = {
        "pyaudio": "PyAudio (audio capture)",
        "numpy": "NumPy (audio processing)",
        "yaml": "PyYAML (configuration)",
        "faster_whisper": "faster-whisper (speech recognition)",
        "pynput": "pynput (keyboard/mouse control)",
        "PIL": "Pillow (image processing)",
        "pystray": "pystray (system tray icon)",
    }

    missing_packages = []

    for module_name, description in required_packages.items():
        try:
            if module_name == "yaml":
                import yaml
            elif module_name == "PIL":
                from PIL import Image
            elif module_name == "faster_whisper":
                from faster_whisper import WhisperModel
            else:
                __import__(module_name)
            print_success(description)
        except ImportError:
            print_error(f"{description} - NOT FOUND")
            missing_packages.append(module_name)

    if missing_packages:
        print()
        print_error("Missing required packages!")
        print("\nInstall missing packages with:")

        # Map module names to pip package names
        pip_packages = {
            "yaml": "pyyaml",
            "PIL": "pillow",
            "faster_whisper": "faster-whisper",
        }

        install_names = [pip_packages.get(pkg, pkg) for pkg in missing_packages]
        print(f"\n  pip install {' '.join(install_names)}")
        print()
        return False

    return True

def check_optional_dependencies():
    """Check optional dependencies and warn if missing."""
    print_header("Checking optional dependencies...")

    optional_packages = {
        "pyautogui": ("PyAutoGUI", "Screen segmentation features will be disabled"),
        "pywinauto": ("pywinauto", "Advanced UI element detection will be disabled (Windows only)"),
        "watchdog": ("watchdog", "Auto-reload on code changes will be disabled"),
        "pyperclip": ("pyperclip", "Clipboard-based text injection will be unavailable"),
    }

    for module_name, (description, warning) in optional_packages.items():
        try:
            __import__(module_name)
            print_success(description)
        except ImportError:
            print_warning(f"{description} - {warning}")

def check_audio_devices():
    """Check if audio input devices are available."""
    print_header("Checking audio devices...")

    try:
        import pyaudio
        p = pyaudio.PyAudio()

        # Check for input devices
        input_devices = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])

        p.terminate()

        if not input_devices:
            print_warning("No audio input devices found")
            print("  You may need to connect a microphone")
            return True  # Not fatal, just a warning

        print_success(f"Found {len(input_devices)} audio input device(s)")
        return True

    except Exception as e:
        print_warning(f"Could not check audio devices: {e}")
        return True  # Not fatal

def validate_config():
    """Validate configuration file structure."""
    print_header("Validating configuration...")

    try:
        from src.core.config import Config
        config = Config("config.yaml")

        # Check critical config sections
        critical_sections = ["hotkeys", "audio", "model", "text_processing"]
        for section in critical_sections:
            if not config.get(section):
                print_error(f"Missing config section: {section}")
                return False

        print_success("Configuration structure valid")
        return True

    except Exception as e:
        print_error(f"Configuration validation failed: {e}")
        return False

def main():
    """Main entry point."""
    print()
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}  Speech-to-Text Dictation Tool - Startup Check  {Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

    # Run all checks
    checks = [
        ("Python version", check_python_version),
        ("Configuration file", check_config_file),
        ("Required dependencies", check_dependencies),
        ("Configuration validation", validate_config),
    ]

    for check_name, check_func in checks:
        if not check_func():
            print()
            print_error(f"Startup check failed: {check_name}")
            print("\nPlease fix the issues above and try again.")
            sys.exit(1)

    # Optional checks (warnings only)
    check_optional_dependencies()
    check_audio_devices()

    # All checks passed
    print()
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}  All checks passed! Starting application...  {Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 60}{Colors.END}")
    print()

    # Import and run the application
    try:
        from src.main import main as run_app
        run_app()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"Fatal error: {e}")
        print("\nFor detailed error information, check the log files.")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
