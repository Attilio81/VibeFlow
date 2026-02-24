import os
import json
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

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
