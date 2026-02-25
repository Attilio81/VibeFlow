# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeFlow is a Windows voice dictation application that transforms speech into formatted, professional text. It combines local Speech-to-Text (faster-whisper with CUDA) and LLM text rewriting to produce clean output in three styles: confidential (casual), formal (professional), and technical (documentation).

## Commands

```bash
# Run the main application (listens for global hotkeys)
python main.py
# Or use the Windows launcher
start_vibeflow.bat

# Run the Gradio test dashboard (http://localhost:7860)
python dashboard.py

# Verify CUDA setup
python test_cuda.py
```

## Architecture

The application follows a pipeline architecture for voice-to-text processing:

```
Hotkey Press → AudioManager → STTService → LLMService → ClipboardManager → Paste
                    ↓
             RecordingIndicator (UI overlay)
```

### Core Components

- **main.py** - Entry point and orchestrator. Registers global hotkeys (CTRL+ALT+1/2/3), coordinates the pipeline via `VibeFlowApp.process_vibe()`, and runs the Tkinter main loop for the overlay.

- **audio_manager.py** - Handles microphone recording with VAD (Voice Activity Detection). Records at 16kHz mono (Whisper's native format), applies noise reduction via `noisereduce`, and bandpass filtering (80Hz-7.5kHz). Auto-stops after configurable silence duration.

- **stt_service.py** - Wrapper around `faster-whisper`. Loads Whisper model with CUDA acceleration, uses `personal_dictionary.txt` as initial prompt context. Falls back to smaller models or CPU if CUDA fails.

- **llm_service.py** - Uses OpenAI SDK to rewrite transcribed text. Supports two providers configured via `LLM_PROVIDER` env var: `lmstudio` (local) or `deepseek` (cloud). Loads style prompts from `profiles.json`. User prompt adapts based on vibe (confidential = "pulisci", others = "formatta").

- **clipboard_manager.py** - Uses Win32 API to backup clipboard, set new text, send Ctrl+V, then restore original clipboard content asynchronously.

- **recording_indicator.py** - Tkinter overlay with real-time waveform visualization driven by audio RMS levels. Shows provider icon (local/cloud) and stop/confirm buttons.

- **dashboard.py** - Gradio web interface for testing audio/transcription, editing profiles and personal dictionary, and controlling the main process.

### Configuration Files

- `.env` - API keys and provider selection (LLM_PROVIDER, DEEPSEEK_API_KEY, LMSTUDIO_BASE_URL, LMSTUDIO_MODEL_ID)
- `profiles.json` - System prompts for the three writing styles (confidential, formal, technical)
- `personal_dictionary.txt` - Custom vocabulary for Whisper (one word per line, # for comments)

### Key Dependencies

- `faster-whisper` with `ctranslate2` - CUDA-accelerated Whisper inference
- `openai` - LLM client for DeepSeek and LMStudio (OpenAI-compatible APIs)
- `sounddevice`/`soundfile` - Audio recording and I/O
- `noisereduce`/`scipy` - Audio preprocessing
- `keyboard` - Global hotkey registration
- `pywin32` - Windows clipboard and window focus management
- `gradio` - Dashboard web UI

## Language

This is an Italian-language application. Code comments, UI text, log messages, and LLM prompts are in Italian. The Whisper model is configured with `language="it"`.
