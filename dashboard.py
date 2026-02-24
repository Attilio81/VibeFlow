import os
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
    gr.Markdown("# 🚀 VibeFlow Testing Dashboard")
    gr.Markdown("Testa il flusso di STT e LLM indipendentemente dalle hotkeys e dalla clipboard.")
    
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

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
