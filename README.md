# Speech-to-Text Dictation Tool

A lightweight, push-to-talk dictation tool that converts speech to text in real-time and types it directly into any application. Optimized for systems with limited VRAM (2GB+) using CPU-first processing with optional GPU acceleration.

## Features

- **Push-to-Talk Interface**: Hold `Ctrl+Win` (or `Ctrl+Cmd` on Mac) to record, release to transcribe
- **Non-Destructive**: Types text directly without using the clipboard
- **Low Resource Usage**: Designed to run on systems with 2GB VRAM using quantized models
- **GPU-Accelerated**: Uses `faster-whisper` with int8 quantization for optimal performance
- **CPU Fallback**: Automatically falls back to CPU if GPU is unavailable
- **Background Operation**: Runs in the background, ready whenever you need it

## Architecture

The tool consists of four independent modules:

1. **Hotkey Listener** (`pynput`): Detects global Ctrl+Win key combination
2. **Audio Capture** (`PyAudio`): Records microphone input in 16kHz mono
3. **STT Engine** (`faster-whisper`): Transcribes audio using Whisper models
4. **Text Injection** (`pynput`): Types the transcribed text at cursor position

## System Requirements

### Minimum Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **RAM**: 2GB available system RAM
- **VRAM**: 2GB for GPU acceleration (optional, will use CPU otherwise)
- **Microphone**: Any system microphone

### Recommended Setup
- **VRAM**: 2GB+ with CUDA support for faster transcription
- **RAM**: 4GB+ for smoother operation
- **Microphone**: Quality microphone for better accuracy

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SpeechToText
```

### 2. Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev
```

#### On macOS:
```bash
brew install portaudio
```

#### On Windows:
PyAudio will be installed via pip (see step 3).

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues installing PyAudio:
- **Windows**: Download a precompiled wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- **macOS/Linux**: Ensure portaudio is installed first (see step 2)

### 4. (Optional) GPU Acceleration Setup

If you have an NVIDIA GPU and want to use CUDA acceleration:

1. Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (version 11.x or 12.x)
2. Install cuDNN (optional but recommended)
3. The tool will automatically detect and use GPU if available

**VRAM Usage**:
- GPU mode (`small.en` with int8): ~1.5GB VRAM
- CPU mode (`tiny.en`): 0GB VRAM, ~500MB RAM

## Usage

### Running the Tool

```bash
python dictation.py
```

Or make it executable:

```bash
chmod +x dictation.py
./dictation.py
```

### Using the Dictation Tool

1. **Start the application**: Run `python dictation.py`
2. **Wait for "Ready!"**: The model needs to load first (5-10 seconds)
3. **Press and hold** `Ctrl+Win` (or `Ctrl+Cmd` on Mac)
4. **Speak your text** clearly into the microphone
5. **Release the keys** to stop recording
6. **Wait** for transcription (typically 1-3 seconds)
7. **Text will be typed** at your cursor position automatically

### Example Workflow

```
1. Open any text editor (Word, Notepad, browser, etc.)
2. Position your cursor where you want text to appear
3. Hold Ctrl+Win and say: "This is a test of the dictation tool."
4. Release keys
5. Text appears: "This is a test of the dictation tool."
```

## Configuration

You can modify the following parameters in `dictation.py`:

### Hotkey Combination
```python
# Change the hotkey (line 24)
HOTKEY_COMBINATION = {keyboard.Key.ctrl, keyboard.Key.cmd}

# Examples:
# Ctrl+Shift: {keyboard.Key.ctrl, keyboard.Key.shift}
# Alt+Space: {keyboard.Key.alt, keyboard.Key.space}
```

### Model Selection
```python
# Change the Whisper model (line 44)
WHISPER_MODEL = WhisperModel("small.en", device="cuda", compute_type="int8")

# Available models (English-only):
# - tiny.en   : Fastest, ~1GB RAM, lower accuracy
# - base.en   : Fast, ~1.5GB RAM, good accuracy
# - small.en  : Balanced, ~2GB RAM, great accuracy (default)
# - medium.en : Slower, ~5GB RAM, excellent accuracy
```

### Audio Settings
```python
# Audio capture settings (lines 30-33)
SAMPLE_RATE = 16000  # Whisper requires 16kHz
CHANNELS = 1         # Mono audio
CHUNK_SIZE = 1024    # Buffer size (lower = less latency)
```

## Troubleshooting

### "Failed to load any model"
- Ensure you have internet connection (models download on first run)
- Check that `faster-whisper` is installed: `pip install faster-whisper`

### "Failed to start recording"
- Check microphone permissions
- Verify PyAudio is installed correctly: `python -c "import pyaudio; print(pyaudio.get_portaudio_version())"`
- On Linux: Add user to `audio` group: `sudo usermod -a -G audio $USER`

### "GPU model failed to load"
- This is normal if you don't have CUDA installed
- The tool will automatically fall back to CPU mode
- To force CPU mode, change `device="cuda"` to `device="cpu"` in line 46

### Hotkey Not Working
- **Windows**: Run as administrator if in a privileged application
- **Linux**: May require X11 or accessibility permissions
- **macOS**: Grant accessibility permissions in System Preferences → Security & Privacy

### Poor Transcription Quality
- Use a better microphone or reduce background noise
- Speak clearly and at a moderate pace
- Upgrade to a larger model (e.g., `medium.en`)
- Ensure audio input level is not too low/high

### High CPU Usage
- Normal during transcription (should drop to near-zero when idle)
- Use GPU acceleration if available
- Switch to a smaller model (e.g., `tiny.en`)

## Technical Details

### Resource Footprint

| Component | VRAM | RAM | Disk |
|-----------|------|-----|------|
| `tiny.en` CPU | 0 MB | ~500 MB | ~75 MB |
| `base.en` CPU | 0 MB | ~750 MB | ~145 MB |
| `small.en` GPU (int8) | ~1.5 GB | ~500 MB | ~470 MB |
| `small.en` CPU | 0 MB | ~2 GB | ~470 MB |

### Performance

Typical transcription times (5-second audio clip):
- `tiny.en` (CPU): ~2-3 seconds
- `small.en` (CPU): ~5-8 seconds
- `small.en` (GPU, int8): ~0.5-1 second

### Design Principles

1. **CPU-First**: Bypasses VRAM limitations by defaulting to CPU processing
2. **Asynchronous**: Hotkey listener runs in separate thread to prevent timeouts
3. **Non-Blocking**: Audio processing happens in worker threads
4. **Non-Destructive**: Uses keyboard simulation instead of clipboard
5. **Fail-Safe**: Graceful fallbacks for GPU/model loading failures

## Project Structure

```
SpeechToText/
├── dictation.py          # Main application
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore rules
```

## Future Enhancements

Potential improvements:
- [ ] Custom wake word support
- [ ] Multiple language support
- [ ] Configurable hotkeys via config file
- [ ] System tray icon with status indicator
- [ ] Audio feedback (beep on start/stop)
- [ ] Continuous dictation mode
- [ ] Custom vocabulary/commands
- [ ] Punctuation commands ("period", "comma", etc.)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[Specify your license here]

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for the optimized implementation
- [pynput](https://github.com/moses-palmer/pynput) for keyboard control
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio capture

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing [Issues](../../issues)
3. Create a new issue with:
   - Your OS and Python version
   - Error messages (full traceback)
   - Steps to reproduce

---

**Note**: This tool is designed for personal productivity and accessibility. Respect privacy laws and obtain consent before recording others' speech.
