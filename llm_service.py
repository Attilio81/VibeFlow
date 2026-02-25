import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger("vibeflow")


class LLMService:
    def __init__(self):
        """Initialize LLM service with configuration from environment variables."""
        self.provider = os.getenv("LLM_PROVIDER", "lmstudio")

        if self.provider == "lmstudio":
            base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
            self.model_id = os.getenv("LMSTUDIO_MODEL_ID", "meta-llama-3.1-8b-instruct")
            self.client = OpenAI(base_url=base_url, api_key="lm-studio")
            logger.info(f"Using LMStudio at {base_url} with model {self.model_id}")

        elif self.provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY not set. Please set it in .env file")
            self.client = OpenAI(base_url="https://api.deepseek.com", api_key=api_key)
            self.model_id = "deepseek-chat"
            logger.info("Using DeepSeek cloud API")

        else:
            raise ValueError(f"Provider '{self.provider}' not supported. Use 'lmstudio' or 'deepseek'")

        profiles_path = os.getenv("PROFILES_PATH", "./profiles.json")
        with open(profiles_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.PROFILES = {name: data["system_prompt"] for name, data in raw.items()}

    def rewrite_text(self, text: str, vibe: str) -> str:
        if not text:
            return ""

        if vibe not in self.PROFILES:
            vibe = "confidential"

        logger.info(f"Rewriting text with vibe: {vibe}...")

        system_prompt = self.PROFILES[vibe]

        # User prompt adattato al vibe
        if vibe == "confidential":
            user_prompt = (
                "Pulisci il seguente testo secondo le tue istruzioni. "
                "Stampa SOLO il testo pulito, nient'altro.\n\n"
                f"TESTO:\n{text}"
            )
        else:
            user_prompt = (
                "Formatta il seguente testo secondo le tue istruzioni. "
                "Stampa SOLO il testo formattato, senza commenti o spiegazioni. "
                "Conserva TUTTE le informazioni del testo originale.\n\n"
                f"TESTO:\n{text}"
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Bassa per output più deterministico
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return text  # fallback to original text if LLM fails
