import keyboard
import time
import threading
import os
from audio_manager import AudioManager
from stt_service import STTService
from llm_service import LLMService
from clipboard_manager import ClipboardManager
from recording_indicator import RecordingIndicator
from dotenv import load_dotenv

load_dotenv()

class VibeFlowApp:
    def __init__(self):
        print("="*60)
        print("🚀 Initializing VibeFlow...")
        print("="*60)
        
        print("\n[1/4] Loading Audio Manager...")
        self.audio_manager = AudioManager()
        print("✓ Audio Manager ready")
        
        print("\n[2/4] Loading STT Service (Whisper model)...")
        print("⏳ This may take 30-60 seconds on first run (downloading model)...")
        self.stt_service = STTService() # uses LLM_PROVIDER from .env or default 'lmstudio'
        print("✓ Whisper model loaded and ready")
        
        print("\n[3/4] Loading LLM Service...")
        self.llm_service = LLMService()
        print("✓ LLM Service ready")
        
        print("\n[4/4] Initializing Recording Indicator...")
        self.clipboard_manager = ClipboardManager()
        self.indicator = RecordingIndicator()
        self.is_processing = False
        
        print("\n" + "="*60)
        print("✅ VibeFlow is ready and running in the background!")
        print("="*60)

    def process_vibe(self, vibe: str):
        if self.is_processing:
            print("Already processing, please wait...")
            return
            
        self.is_processing = True
        
        try:
            print(f"\n--- Starting VibeFlow ({vibe} mode) ---")
            
            # Show recording indicator
            self.indicator.show()
            
            # 1. Record Audio (with stop callback)
            audio_file = self.audio_manager.record_audio(
                stop_callback=lambda: self.indicator.stop_recording
            )
            if not audio_file:
                print("No audio recorded. Aborting.")
                self.indicator.update_status("error")
                return

            # 2. Transcribe (STT)
            self.indicator.update_status("processing")
            transcribed_text = self.stt_service.transcribe(audio_file)
            if not transcribed_text:
                print("Transcription failed or empty. Aborting.")
                self.indicator.update_status("error")
                return

            # 3. Rewrite (LLM)
            final_text = self.llm_service.rewrite_text(transcribed_text, vibe)
            if not final_text:
                print("Rewriting failed. Aborting.")
                self.indicator.update_status("error")
                return

            print(f"Final output: {final_text}")

            # 4. Hide overlay
            self.indicator.hide()
            
            # 5. Restore focus to original window (already done by Stop button)
            # Additional small delay to ensure focus is stable
            time.sleep(0.3)
            
            # 6. Paste to user's active window
            self.clipboard_manager.paste_text(final_text)
            
            # 7. Success feedback (audio only)
            self.audio_manager.play_sound("success")
            print("--- VibeFlow complete ---")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            self.indicator.update_status("error")
        finally:
            self.is_processing = False

    def run(self):
        print("\nRegistered Hotkeys:")
        print("CTRL+ALT+1 -> Confidential")
        print("CTRL+ALT+2 -> Formal")
        print("CTRL+ALT+3 -> Technical")
        print("Press ESC to exit.\n")
        
        # We use threading so the hotkey listener doesn't block the execution
        keyboard.add_hotkey('ctrl+alt+1', lambda: threading.Thread(target=self.process_vibe, args=("confidential",), daemon=True).start())
        keyboard.add_hotkey('ctrl+alt+2', lambda: threading.Thread(target=self.process_vibe, args=("formal",), daemon=True).start())
        keyboard.add_hotkey('ctrl+alt+3', lambda: threading.Thread(target=self.process_vibe, args=("technical",), daemon=True).start())
        
        # Keep Tkinter main loop running if overlay is available
        if self.indicator.window:
            print("Visual overlay active!")
            # Run tkinter update loop
            def check_exit():
                if keyboard.is_pressed('esc'):
                    self.indicator.window.quit()
                else:
                    self.indicator.window.after(100, check_exit)
            
            self.indicator.window.after(100, check_exit)
            self.indicator.window.mainloop()
        else:
            print("Using Windows notifications for status updates.")
            keyboard.wait('esc')

if __name__ == "__main__":
    app = VibeFlowApp()
    app.run()
