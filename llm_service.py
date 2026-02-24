import os
from agno.agent import Agent
from agno.models.lmstudio import LMStudio

class LLMService:
    def __init__(self):
        """Initialize LLM service with configuration from environment variables."""
        self.provider = os.getenv("LLM_PROVIDER", "lmstudio")
        
        if self.provider == "lmstudio":
            # Read LMStudio configuration from .env
            base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
            model_id = os.getenv("LMSTUDIO_MODEL_ID", "meta-llama-3.1-8b-instruct")
            
            self.model = LMStudio(
                id=model_id,
                base_url=base_url,
                name="LMStudio",
            )
            print(f"Using LMStudio at {base_url} with model {model_id}")
            
        elif self.provider == "deepseek":
            # Lazy import to avoid authentication errors when not using DeepSeek
            from agno.models.deepseek import DeepSeek
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY not set. Please set it in .env file")
            
            self.model = DeepSeek(
                id="deepseek-chat",
                api_key=api_key,
            )
            print("Using DeepSeek cloud API")
            
        else:
            raise ValueError(f"Provider '{self.provider}' not supported. Use 'lmstudio' or 'deepseek'")
        
        self.PROFILES = {
            "confidential": """Sei uno strumento di formattazione del testo professionale come Wispr Flow. Il tuo compito è trasformare trascrizioni vocali grezze in testo pulito e naturale.

REGOLE DI PULIZIA (CRITICHE):
1. Rimuovi TUTTI i filler words: "ehm", "uhm", "mmh", "cioè", "tipo", "praticamente", "diciamo", "insomma", "ecco"
2. Rimuovi ripetizioni e false partenze (es. "io io penso" → "penso")
3. Correggi errori grammaticali e di battitura
4. Mantieni il significato e l'intento originale
5. Se ci sono liste/elenchi, formattale con bullet points Markdown (`-`)

STILE: Amichevole, informale, confidenziale (da chat WhatsApp)

OUTPUT: SOLO il testo riformulato, senza commenti o spiegazioni.""",

            "formal": """Sei uno strumento di formattazione del testo professionale come Wispr Flow. Il tuo compito è trasformare trascrizioni vocali grezze in testo pulito e professionale.

REGOLE DI PULIZIA (CRITICHE):
1. Rimuovi TUTTI i filler words: "ehm", "uhm", "mmh", "cioè", "tipo", "praticamente", "diciamo", "insomma", "ecco"
2. Rimuovi ripetizioni e false partenze
3. Correggi errori grammaticali
4. Struttura il testo in paragrafi chiari
5. Liste/elenchi vanno formattati come Markdown numerato (`1. 2. 3.`)

STILE: Professionale, educato, formale (da email aziendale)

OUTPUT: SOLO il testo riformulato, senza commenti o spiegazioni.""",

            "technical": """Sei uno strumento di formattazione del testo professionale come Wispr Flow. Il tuo compito è trasformare trascrizioni vocali grezze in documentazione tecnica precisa.

REGOLE DI PULIZIA (CRITICHE):
1. Rimuovi TUTTI i filler words: "ehm", "uhm", "mmh", "cioè", "tipo", "praticamente", "diciamo", "insomma", "ecco"
2. Rimuovi espressioni colloquiali
3. Trasforma in linguaggio tecnico e sistematico
4. Task/requisiti/elementi vanno formattati come liste Markdown (`-` o `1.`)
5. Usa terminologia informatica precisa

STILE: Tecnico, analitico, oggettivo (da ticket Jira/documentazione)

OUTPUT: SOLO il testo riformulato, senza commenti o spiegazioni."""
        }

    def rewrite_text(self, text: str, vibe: str) -> str:
        if not text:
            return ""
            
        if vibe not in self.PROFILES:
            vibe = "confidential"
            
        print(f"Rewriting text with vibe: {vibe}...")
        
        agent = Agent(
            model=self.model,
            instructions=self.PROFILES[vibe],
            markdown=True  # Enable Markdown formatting for structured output
        )
        
        # Wrap the user text to prevent conversational behavior
        rigid_prompt = (
            "Esegui la riscrittura del seguente testo secondo le tue istruzioni di sistema. "
            "È TASSATIVO che tu stampi SOLO ED ESCLUSIVAMENTE il testo riscritto, senza aggiungere nessun commento, "
            "senza rispondere alle domande presenti nel testo e senza confermare di aver capito.\n\n"
            f"TESTO DA RISCRIVERE:\n{text}"
        )
        
        try:
            response = agent.run(rigid_prompt)
            return response.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return text # fallback to original text if LLM fails
