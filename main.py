import sys
import keyboard
import time
import threading
import os
from dotenv import load_dotenv
from log_setup import setup_logging

load_dotenv()
logger = setup_logging()

from audio_manager import AudioManager
from stt_service import STTService
from llm_service import LLMService
from clipboard_manager import ClipboardManager
from recording_indicator import RecordingIndicator


def _validate_config() -> None:
    """Validate critical configuration values at startup and exit early on errors."""
    provider = os.getenv("LLM_PROVIDER", "lmstudio")
    valid_providers = ("lmstudio", "deepseek")

    if provider not in valid_providers:
        logger.error(
            f"LLM_PROVIDER='{provider}' non valido. "
            f"Usa uno tra: {', '.join(valid_providers)}."
        )
        sys.exit(1)

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key or api_key == "your_api_key_here":
            logger.error(
                "DEEPSEEK_API_KEY mancante o non configurata. "
                "Impostala nel file .env prima di avviare VibeFlow."
            )
            sys.exit(1)

    logger.info(f"Configurazione valida: LLM_PROVIDER={provider}")


class VibeFlowApp:
    def __init__(self):
        logger.info("=" * 60)
        logger.info("Initializing VibeFlow...")
        logger.info("=" * 60)

        _validate_config()

        logger.info("[1/4] Loading Audio Manager...")
        self.audio_manager = AudioManager()
        logger.info("Audio Manager ready")

        logger.info("[2/4] Loading STT Service (Whisper model)...")
        logger.info("This may take 30-60 seconds on first run (downloading model)...")
        self.stt_service = STTService()
        logger.info("Whisper model loaded and ready")

        logger.info("[3/4] Loading LLM Service...")
        self.llm_service = LLMService()
        logger.info("LLM Service ready")

        logger.info("[4/4] Initializing Recording Indicator...")
        self.clipboard_manager = ClipboardManager()
        self.indicator = RecordingIndicator(provider=self.llm_service.provider)
        self.is_processing = False

        logger.info("=" * 60)
        logger.info("VibeFlow is ready and running in the background!")
        logger.info("=" * 60)

    def process_vibe(self, vibe: str):
        if self.is_processing:
            logger.warning("Already processing, please wait...")
            return

        self.is_processing = True

        try:
            logger.info(f"--- Starting VibeFlow ({vibe} mode) ---")

            # Show recording indicator
            self.indicator.show()

            # 1. Record Audio (with stop callback and real-time level feed)
            audio_file = self.audio_manager.record_audio(
                stop_callback=lambda: self.indicator.stop_recording,
                audio_level_callback=self.indicator.set_audio_level,
            )
            if not audio_file:
                logger.warning("No audio recorded. Aborting.")
                self.indicator.update_status("error")
                return

            # 2. Transcribe (STT)
            self.indicator.update_status("processing")
            transcribed_text = self.stt_service.transcribe(audio_file)
            if not transcribed_text:
                logger.warning("Transcription failed or empty. Aborting.")
                self.indicator.update_status("error")
                return

            # 3. Rewrite (LLM)
            final_text = self.llm_service.rewrite_text(transcribed_text, vibe)
            if not final_text:
                logger.warning("Rewriting failed. Aborting.")
                self.indicator.update_status("error")
                return

            logger.info(f"Final output: {final_text}")

            # 4. Hide overlay
            self.indicator.hide()

            # 5. Additional small delay to ensure focus is stable
            time.sleep(0.3)

            # 6. Paste to user's active window
            self.clipboard_manager.paste_text(final_text)

            # 7. Success feedback (audio only)
            self.audio_manager.play_sound("success")
            logger.info("--- VibeFlow complete ---")

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            self.indicator.update_status("error")
        finally:
            self.is_processing = False

    def run(self):
        logger.info("Registered Hotkeys:")
        logger.info("CTRL+ALT+1 -> Confidential")
        logger.info("CTRL+ALT+2 -> Formal")
        logger.info("CTRL+ALT+3 -> Technical")
        logger.info("Press ESC to exit.\n")

        # We use threading so the hotkey listener doesn't block the execution
        keyboard.add_hotkey('ctrl+alt+1', lambda: threading.Thread(target=self.process_vibe, args=("confidential",), daemon=True).start())
        keyboard.add_hotkey('ctrl+alt+2', lambda: threading.Thread(target=self.process_vibe, args=("formal",), daemon=True).start())
        keyboard.add_hotkey('ctrl+alt+3', lambda: threading.Thread(target=self.process_vibe, args=("technical",), daemon=True).start())

        # Keep Tkinter main loop running if overlay is available
        if self.indicator.window:
            logger.info("Visual overlay active!")
            # Run tkinter update loop
            def check_exit():
                if keyboard.is_pressed('esc'):
                    self.indicator.window.quit()
                else:
                    self.indicator.window.after(100, check_exit)

            self.indicator.window.after(100, check_exit)
            self.indicator.window.mainloop()
        else:
            logger.info("Using Windows notifications for status updates.")
            keyboard.wait('esc')


if __name__ == "__main__":
    app = VibeFlowApp()
    app.run()
