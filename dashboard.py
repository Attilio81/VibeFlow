import os
import sys
import json
import subprocess
import threading
import gradio as gr
from dotenv import load_dotenv
from stt_service import STTService
from llm_service import LLMService

# Load environment variables from .env file
load_dotenv()

print("Initializing Dashboard Services...")
stt_service = STTService()
llm_service = LLMService()
print("Services Initialized.")

PROFILES_PATH = os.getenv("PROFILES_PATH", "./profiles.json")
PERSONAL_DICT_PATH = os.getenv("PERSONAL_DICT_PATH", "./personal_dictionary.txt")
MAIN_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")

# --- Process management state ---
_main_process: subprocess.Popen | None = None
_log_buffer: list[str] = []
_log_lock = threading.Lock()
MAX_LOG_LINES = 500


def _read_output(proc: subprocess.Popen) -> None:
    """Background thread: reads stdout/stderr from the child process."""
    try:
        for raw_line in iter(proc.stdout.readline, b""):
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            with _log_lock:
                _log_buffer.append(line)
                if len(_log_buffer) > MAX_LOG_LINES:
                    _log_buffer.pop(0)
    except ValueError:
        pass  # pipe closed


def start_main() -> str:
    """Launch main.py as a subprocess."""
    global _main_process
    if _main_process and _main_process.poll() is None:
        return "⚠️ VibeFlow è già in esecuzione"
    with _log_lock:
        _log_buffer.clear()
    _main_process = subprocess.Popen(
        [sys.executable, MAIN_SCRIPT_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=os.path.dirname(MAIN_SCRIPT_PATH),
    )
    t = threading.Thread(target=_read_output, args=(_main_process,), daemon=True)
    t.start()
    return "✅ VibeFlow avviato"


def stop_main() -> str:
    """Terminate the main.py subprocess."""
    global _main_process
    if not _main_process or _main_process.poll() is not None:
        return "⚠️ VibeFlow non è in esecuzione"
    _main_process.terminate()
    try:
        _main_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _main_process.kill()
    return "🛑 VibeFlow fermato"


def get_process_status() -> str:
    if _main_process and _main_process.poll() is None:
        return "🟢 In esecuzione  (PID: " + str(_main_process.pid) + ")"
    return "🔴 Fermo"


def get_logs() -> str:
    with _log_lock:
        return "\n".join(_log_buffer)

def load_profiles():
    """Load profiles from JSON file."""
    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        return (
            profiles.get("confidential", {}).get("system_prompt", ""),
            profiles.get("formal", {}).get("system_prompt", ""),
            profiles.get("technical", {}).get("system_prompt", ""),
            "✅ Profili caricati correttamente"
        )
    except Exception as e:
        return "", "", "", f"❌ Errore nel caricamento: {str(e)}"

def save_profiles(confidential_prompt, formal_prompt, technical_prompt):
    """Save profiles to JSON file."""
    try:
        profiles = {
            "confidential": {
                "system_prompt": confidential_prompt
            },
            "formal": {
                "system_prompt": formal_prompt
            },
            "technical": {
                "system_prompt": technical_prompt
            }
        }
        
        with open(PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        
        # Reload LLM service to pick up new profiles
        global llm_service
        llm_service = LLMService()
        
        return "✅ Profili salvati e ricaricati con successo!"
    except Exception as e:
        return f"❌ Errore nel salvataggio: {str(e)}"

def load_dictionary():
    """Load personal dictionary from file."""
    try:
        with open(PERSONAL_DICT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return content, "✅ Dizionario caricato correttamente"
    except Exception as e:
        return "", f"❌ Errore nel caricamento: {str(e)}"

def save_dictionary(content):
    """Save personal dictionary to file."""
    try:
        with open(PERSONAL_DICT_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        # Reload STT service so the new words are picked up
        global stt_service
        stt_service = STTService()
        return "✅ Dizionario salvato e STT ricaricato con successo!"
    except Exception as e:
        return f"❌ Errore nel salvataggio: {str(e)}"

def update_provider(provider):
    global llm_service
    # LLMService reads LLM_PROVIDER from env – set it before instantiating
    os.environ["LLM_PROVIDER"] = provider.lower()
    llm_service = LLMService()
    return f"Provider impostato su {provider}"

def process_audio(audio_path, vibe):
    if not audio_path:
        return "Nessun audio fornito.", ""
        
    print(f"Processing audio: {audio_path} with vibe: {vibe}")
    
    # 1. Transcribe
    transcription = stt_service.transcribe(audio_path)
    if not transcription:
        return "Errore nella trascrizione o audio vuoto.", ""
        
    # 2. Rewrite
    mapping = {
        "Confidenziale": "confidential",
        "Formale": "formal",
        "Tecnico": "technical"
    }
    vibe_key = mapping.get(vibe, "confidential")
    
    final_text = llm_service.rewrite_text(transcription, vibe_key)
    
    return transcription, final_text

with gr.Blocks(title="VibeFlow Dashboard") as demo:
    gr.Markdown("# 🚀 VibeFlow Dashboard")
    gr.Markdown("Testa il flusso di STT e LLM, e configura i profili di scrittura.")
    
    with gr.Tabs():
        # Tab 1: Audio Testing
        with gr.Tab("🎤 Test Audio"):
            gr.Markdown("### Testa il flusso di STT e LLM indipendentemente dalle hotkeys e dalla clipboard.")
            
            with gr.Row():
                with gr.Column(scale=1):
                    provider_dropdown = gr.Dropdown(
                        choices=["LMStudio", "DeepSeek"],
                        value="LMStudio",
                        label="Seleziona il Provider LLM"
                    )
                    provider_status = gr.Textbox(label="Status", value="Provider impostato su LMStudio", interactive=False)
                    provider_dropdown.change(fn=update_provider, inputs=provider_dropdown, outputs=provider_status)
                    
                    audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Registra o Carica Audio")
                    vibe_dropdown = gr.Dropdown(
                        choices=["Confidenziale", "Formale", "Tecnico"], 
                        value="Confidenziale", 
                        label="Seleziona il Vibe"
                    )
                    submit_btn = gr.Button("Elabora", variant="primary")
                    
                with gr.Column(scale=2):
                    transcription_output = gr.Textbox(label="1. Trascrizione Grezza (faster-whisper)", lines=3)
                    final_output = gr.Textbox(label="2. Output Formattato (LLM)", lines=6)
                    
            submit_btn.click(
                fn=process_audio,
                inputs=[audio_input, vibe_dropdown],
                outputs=[transcription_output, final_output]
            )
        
        # Tab 2: Profile Editor
        with gr.Tab("⚙️ Editor Profili"):
            gr.Markdown("### Modifica i prompt di sistema per ogni stile di scrittura")
            gr.Markdown("I profili vengono salvati in `profiles.json` e ricaricati automaticamente.")
            
            with gr.Row():
                load_btn = gr.Button("🔄 Carica Profili", variant="secondary")
            
            with gr.Row():
                status_text = gr.Textbox(label="Status", interactive=False)
            
            with gr.Column():
                gr.Markdown("#### 📝 Confidenziale (CTRL+ALT+1)")
                confidential_textbox = gr.Textbox(
                    label="System Prompt",
                    lines=10,
                    placeholder="Inserisci il prompt di sistema per lo stile confidenziale..."
                )
                
                gr.Markdown("#### 💼 Formale (CTRL+ALT+2)")
                formal_textbox = gr.Textbox(
                    label="System Prompt",
                    lines=10,
                    placeholder="Inserisci il prompt di sistema per lo stile formale..."
                )
                
                gr.Markdown("#### 🔧 Tecnico (CTRL+ALT+3)")
                technical_textbox = gr.Textbox(
                    label="System Prompt",
                    lines=10,
                    placeholder="Inserisci il prompt di sistema per lo stile tecnico..."
                )
            
            with gr.Row():
                save_btn = gr.Button("💾 Salva Profili", variant="primary", size="lg")
            
            # Load profiles on button click
            load_btn.click(
                fn=load_profiles,
                inputs=[],
                outputs=[confidential_textbox, formal_textbox, technical_textbox, status_text]
            )
            
            # Save profiles on button click
            save_btn.click(
                fn=save_profiles,
                inputs=[confidential_textbox, formal_textbox, technical_textbox],
                outputs=[status_text]
            )
            
            # Auto-load profiles on dashboard startup
            demo.load(
                fn=load_profiles,
                inputs=[],
                outputs=[confidential_textbox, formal_textbox, technical_textbox, status_text]
            )

        # Tab 3: Personal Dictionary Editor
        with gr.Tab("📖 Dizionario Personale"):
            gr.Markdown("### Gestisci il dizionario personale per migliorare l'accuratezza di Whisper")
            gr.Markdown(
                "Aggiungi parole personalizzate (nomi propri, termini tecnici, acronimi) — una per riga.\n"
                "Le righe che iniziano con `#` sono commenti e vengono ignorate da Whisper."
            )

            with gr.Row():
                dict_load_btn = gr.Button("🔄 Carica Dizionario", variant="secondary")

            with gr.Row():
                dict_status = gr.Textbox(label="Status", interactive=False)

            dict_textbox = gr.Textbox(
                label="Contenuto del dizionario personale",
                lines=20,
                placeholder="# Aggiungi parole qui\nNomeAzienda\nTermineTecnico\n..."
            )

            with gr.Row():
                dict_save_btn = gr.Button("💾 Salva Dizionario", variant="primary", size="lg")

            dict_load_btn.click(
                fn=load_dictionary,
                inputs=[],
                outputs=[dict_textbox, dict_status]
            )

            dict_save_btn.click(
                fn=save_dictionary,
                inputs=[dict_textbox],
                outputs=[dict_status]
            )

            demo.load(
                fn=load_dictionary,
                inputs=[],
                outputs=[dict_textbox, dict_status]
            )

        # Tab 4: VibeFlow Control
        with gr.Tab("▶️ Controllo VibeFlow"):
            gr.Markdown("### Avvia e ferma il processo principale di VibeFlow")
            gr.Markdown(
                "Utilizza i pulsanti per avviare/fermare `main.py`. "
                "I log vengono aggiornati automaticamente ogni 2 secondi."
            )

            with gr.Row():
                start_btn = gr.Button("▶️ Avvia VibeFlow", variant="primary", size="lg")
                stop_btn = gr.Button("⏹️ Ferma VibeFlow", variant="stop", size="lg")

            with gr.Row():
                process_status = gr.Textbox(
                    label="Stato processo",
                    value=get_process_status,
                    interactive=False,
                )
                action_status = gr.Textbox(label="Ultimo comando", interactive=False)

            log_console = gr.Textbox(
                label="Console log (ultimi 500 righe)",
                lines=25,
                max_lines=25,
                interactive=False,
                autoscroll=True,
            )

            start_btn.click(fn=start_main, inputs=[], outputs=[action_status])
            stop_btn.click(fn=stop_main, inputs=[], outputs=[action_status])

            # Auto-refresh every 2 seconds
            timer = gr.Timer(value=2)
            timer.tick(fn=get_logs, inputs=[], outputs=[log_console])
            timer.tick(fn=get_process_status, inputs=[], outputs=[process_status])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
