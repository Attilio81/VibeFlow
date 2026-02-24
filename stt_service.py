from faster_whisper import WhisperModel
import os
import logging
from cuda_utils import add_nvidia_dll_paths

add_nvidia_dll_paths()

logger = logging.getLogger("vibeflow")


class STTService:
    def __init__(self, model_size="medium", device="cuda", compute_type="float16"):
        logger.info(f"Loading Whisper model '{model_size}' on {device}...")
        try:
            # medium: best balance between speed and accuracy for Italian
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logger.warning(f"Failed to load {model_size} on {device}: {e}. Trying 'small'...")
            try:
                self.model = WhisperModel("small", device=device, compute_type=compute_type)
            except Exception:
                logger.warning("Falling back to 'base' on CPU...")
                self.model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")

        # Load personal dictionary from file
        self.personal_dictionary = self._load_personal_dictionary()
        logger.info(f"Loaded {len(self.personal_dictionary)} custom words from personal dictionary")

    def _load_personal_dictionary(self):
        """Load custom words from personal_dictionary.txt"""
        dictionary_file = "personal_dictionary.txt"
        words = []

        try:
            with open(dictionary_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        words.append(line)
        except FileNotFoundError:
            logger.warning(f"{dictionary_file} not found. Using built-in fallback dictionary.")
            # Default words
            words = [
                "WebService",
                "Netesa",
                "installare",
                "LMStudio",
                "VibeFlow"
            ]

        return words

    def transcribe(self, audio_file: str) -> str:
        if not audio_file or not os.path.exists(audio_file):
            return ""

        logger.info("Transcribing with optimized parameters (Wispr Flow-inspired)...")

        # Build initial prompt with personal dictionary and context
        initial_prompt = (
            "Trascrizione accurata in italiano. "
            "Pronuncia chiara e naturale. "
            f"Dizionario personalizzato: {', '.join(self.personal_dictionary)}. "
            "Termini comuni: email, meeting, progetto, team, deadline, task."
        )

        # Optimized parameters inspired by Wispr Flow and Whisper best practices
        segments, info = self.model.transcribe(
            audio_file,
            language="it",
            beam_size=5,              # Beam search for better accuracy
            best_of=5,                # Sample multiple candidates
            temperature=0.0,          # Deterministic (0.0) for consistency
            compression_ratio_threshold=2.4,
            log_prob_threshold=-0.7,  # Less aggressive filtering
            no_speech_threshold=0.4,  # Lower to catch more speech
            condition_on_previous_text=True,  # Use context
            vad_filter=True,          # VAD to remove silent parts
            vad_parameters=dict(
                threshold=0.4,
                min_speech_duration_ms=100,
                min_silence_duration_ms=500
            ),
            word_timestamps=False,    # Faster without word-level timestamps
            initial_prompt=initial_prompt,
            hallucination_silence_threshold=1.0  # Prevent hallucinations
        )

        # Combine segments
        text = " ".join([segment.text.strip() for segment in segments])
        logger.info(f"Raw transcription: {text}")

        # Clean up temp file
        try:
            os.remove(audio_file)
            logger.debug(f"Temp file removed: {audio_file}")
        except Exception as e:
            logger.warning(f"Could not remove temp file {audio_file}: {e}")

        return text.strip()
