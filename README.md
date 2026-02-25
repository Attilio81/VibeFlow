# 🎤 VibeFlow

**VibeFlow** è un'applicazione intelligente di dettatura vocale per Windows che trasforma il tuo parlato in testo formattato e professionale. Ispirato a **Wispr Flow**, VibeFlow combina Speech-to-Text ad alta precisione con AI per riscrivere automaticamente ciò che detti secondo lo stile desiderato.

## ✨ Caratteristiche

- 🎯 **Hotkey globali** - Registra in qualsiasi applicazione con `CTRL+ALT+1/2/3`
- 🎨 **3 stili di scrittura** - Confidenziale, Formale, Tecnico
- 🧠 **AI-powered** - Rimuove automaticamente riempitivi ("ehm", "uhm"), formatta liste e corregge grammatica
- 🚀 **CUDA accelerato** - Whisper medium model su GPU per trascrizioni veloci e precise
- 🎙️ **VAD intelligente** - Voice Activity Detection con 3 secondi di pausa automatica
- 🔒 **Privacy-first** - Tutto locale su GPU, opzionale cloud (DeepSeek)
- 📝 **Dizionario personalizzato** - Aggiungi termini tecnici e nomi propri
- 🎬 **UI moderna** - Overlay animato con waveform in tempo reale
- 📋 **Paste automatico** - Il testo viene incollato dove stavi scrivendo

## 🖥️ UI Overlay

Durante la registrazione appare un elegante overlay con waveform animata:

- **✕ (Stop)** - Ferma la registrazione e processa l'audio
- **✓ (Conferma)** - Conferma e continua (stesso comportamento di Stop)
- **Animazione waveform** - Barre bianche che si muovono con la tua voce
- **Indicatori di stato** - Cambio colore durante processing (arancione → verde/rosso)
- **Indicatore provider** - 💻 per LMStudio locale, ☁️ per DeepSeek cloud (sempre visibile)

## 🏗️ Architettura

```
VibeFlow/
├── main.py                    # Entry point + hotkey listeners
├── audio_manager.py           # Recording + VAD + preprocessing
├── stt_service.py             # Faster-Whisper (CUDA) transcription
├── llm_service.py             # OpenAI SDK + text formatting
├── clipboard_manager.py       # Windows clipboard integration
├── recording_indicator.py     # Animated overlay UI
├── dashboard.py               # Gradio test interface
├── personal_dictionary.txt    # Custom vocabulary
├── test_cuda.py               # CUDA verification script
├── start_vibeflow.bat         # Windows launcher script
├── .env                       # Configuration (git-ignored)
├── .env.example               # Configuration template
└── requirements.txt           # Python dependencies
```

## 📋 Prerequisiti

### Hardware
- **GPU NVIDIA** con CUDA support (per accelerazione Whisper)
- **Microfono** funzionante

### Software
- **Python 3.10+** (testato su 3.13.2)
- **CUDA Toolkit** (le librerie CUDA vengono installate via pip)
- **LM Studio** (opzionale, solo se usi LLM locale invece di DeepSeek)

## 🚀 Installazione

### 1. Clone del repository

```bash
git clone https://github.com/Attilio81/VibeFlow.git
cd VibeFlow
```

### 2. Crea virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Installa dipendenze

```bash
pip install -r requirements.txt
```

### 4. Configura environment variables

Copia `.env.example` in `.env` e configura:

```bash
cp .env.example .env
```

Modifica `.env`:

```env
# Scegli provider: "deepseek" (cloud) o "lmstudio" (locale)
LLM_PROVIDER=deepseek

# Se usi DeepSeek (consigliato per velocità)
DEEPSEEK_API_KEY=sk-your-api-key-here

# Se usi LM Studio (privacy totale, ma più lento)
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL_ID=meta-llama-3.1-8b-instruct
```

**Per ottenere API key DeepSeek:**
1. Vai su [platform.deepseek.com](https://platform.deepseek.com)
2. Registrati/Login
3. Vai su API Keys → Crea nuova chiave
4. Copia la chiave in `.env`

**Per configurare LM Studio:**
1. Scarica e installa [LM Studio](https://lmstudio.ai/)
2. Carica un modello compatibile (es. Llama-3-8B, Mistral-7B)
3. Avvia il server locale (porta 1234)
4. Imposta `LLM_PROVIDER=lmstudio` in `.env`
5. (Opzionale) Modifica `LMSTUDIO_MODEL_ID` se usi un modello diverso

### 5. (Opzionale) Verifica CUDA

```bash
python test_cuda.py
```

Dovresti vedere:
```
✓ CUDA libraries loaded successfully
```

## 🎯 Utilizzo

### Avvia l'applicazione principale

**Opzione 1: Doppio click (Windows)**
```
start_vibeflow.bat
```

**Opzione 2: Da terminale**
```bash
python main.py
```

L'app si avvia in background e ascolta gli hotkey globali.

### Hotkey disponibili

| Hotkey | Vibe | Descrizione |
|--------|------|-------------|
| `CTRL+ALT+1` | **Confidenziale** | Stile amichevole e colloquiale (WhatsApp, chat) |
| `CTRL+ALT+2` | **Formale** | Stile professionale (email, documenti) |
| `CTRL+ALT+3` | **Tecnico** | Stile preciso e strutturato (documentazione, report) |

### Workflow tipico

1. **Posizionati** dove vuoi scrivere (Word, browser, Notepad, etc.)
2. **Premi** `CTRL+ALT+1` (o 2/3)
3. **Parla** - Apparirà l'overlay con waveform animata e l'icona del provider (💻 o ☁️)
4. **Finisci** - Clicca **✕ Stop** oppure attendi 3 secondi di silenzio
5. **Automatico** - Il testo viene trascritto, formattato e incollato dove stavi scrivendo

### Dashboard di test

Per testare audio e trascrizioni senza usare hotkey:

```bash
python dashboard.py
```

Si apre un'interfaccia web Gradio su `http://localhost:7860` con quattro sezioni:

- **🎤 Test Audio** - Testa trascrizione e formattazione senza usare hotkey
- **⚙️ Editor Profili** - Modifica i system prompt dei tre stili di scrittura
- **📖 Dizionario Personale** - Modifica `personal_dictionary.txt` direttamente dalla UI
- **▶️ Controllo VibeFlow** - Avvia/ferma `main.py` e visualizza i log in tempo reale

#### Editor Profili

L'editor profili ti permette di:
- 📝 Visualizzare e modificare i prompt di sistema per ogni stile (Confidenziale, Formale, Tecnico)
- 💾 Salvare le modifiche in `profiles.json`
- 🔄 Ricaricare automaticamente l'LLM Service con i nuovi prompt
- ⚡ Auto-caricamento dei profili all'apertura della dashboard

Questo rende facile personalizzare il comportamento dell'AI senza modificare manualmente file JSON.

#### Dizionario Personale

Permette di modificare e salvare `personal_dictionary.txt` direttamente dal browser. Al salvataggio, il servizio STT viene ricaricato automaticamente per applicare subito le nuove parole.

#### Controllo VibeFlow

Consente di gestire il processo principale senza aprire un terminale separato:
- ▶️ **Avvia** `main.py` come sottoprocesso
- ⏹️ **Ferma** il processo in modo pulito
- 📋 **Console log** aggiornata automaticamente ogni 2 secondi con stdout/stderr di `main.py`
- 🟢 **Indicatore di stato** con PID del processo

## 🎨 Stili di Vibe

### 1️⃣ Confidenziale (CTRL+ALT+1)
- Tono amichevole e naturale
- Rimuove riempitivi ("tipo", "cioè")
- Ideale per: chat, messaggi informali

**Esempio:**
```
Input:  "Ehm ciao, allora tipo volevo sapere se ci vediamo domani"
Output: "Ciao, volevo sapere se ci vediamo domani"
```

### 2️⃣ Formale (CTRL+ALT+2)
- Tono professionale e cortese
- Struttura ben organizzata
- Ideale per: email, lettere, proposte

**Esempio:**
```
Input:  "Buongiorno, volevo chiedere informazioni sul prodotto"
Output: "Buongiorno,

scrivo per richiedere informazioni riguardo al prodotto.

Resto in attesa di un Vostro cortese riscontro.

Cordiali saluti"
```

### 3️⃣ Tecnico (CTRL+ALT+3)
- Linguaggio preciso e strutturato
- Formatta liste e punti elenco
- Ideale per: documentazione, specifiche, report

**Esempio:**
```
Input:  "Dobbiamo implementare tre funzionalità: autenticazione utente, gestione errori, logging"
Output: "## Requisiti

Il sistema deve implementare le seguenti funzionalità:

1. **Autenticazione utente** - Sistema di login sicuro
2. **Gestione errori** - Error handling robusto
3. **Logging** - Sistema di tracciamento eventi"
```

## 📝 Dizionario Personalizzato

Puoi aggiungere termini tecnici, nomi propri o acronimi al file `personal_dictionary.txt`.

**Tramite Dashboard (consigliato):**
```bash
python dashboard.py
```
Vai su **📖 Dizionario Personale** e modifica direttamente dal browser. Il salvataggio ricarica STT automaticamente.

**Manualmente** — modifica `personal_dictionary.txt`:
```
WebService
LMStudio
VibeFlow
API
CRUD
REST
```

Le righe che iniziano con `#` sono commenti e vengono ignorate. Whisper userà questi termini come contesto per migliorare la trascrizione.

## 🔧 Configurazione Avanzata

### Audio Manager

Modifica parametri in `audio_manager.py`:

```python
self.silence_duration = 3.0      # Secondi di silenzio prima di fermarsi
self.silence_threshold = 0.015   # Soglia RMS per rilevare silenzio
self.max_duration = 60           # Durata massima registrazione (secondi)
```

### STT Service

Cambia modello Whisper in `stt_service.py`:

```python
model = WhisperModel(
    "medium",           # Opzioni: tiny, base, small, medium, large
    device="cuda",
    compute_type="float16"
)
```

**Trade-off modelli:**
- `tiny` - Veloce ma impreciso (~1GB VRAM)
- `base` - Buon compromesso (~1.5GB VRAM)
- `small` - Accurato (~2GB VRAM)
- `medium` - **Consigliato** - Molto accurato (~5GB VRAM) ✅
- `large` - Massima precisione (~10GB VRAM)

### LLM Configuration

Tutte le configurazioni LLM sono gestite tramite `.env`:

```env
# Scegli il provider
LLM_PROVIDER=deepseek          # o "lmstudio"

# DeepSeek (cloud)
DEEPSEEK_API_KEY=sk-xxx

# LM Studio (locale)
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL_ID=meta-llama-3.1-8b-instruct
```

Non è necessario modificare il codice per cambiare provider o configurazione - tutto è parametrizzato nel file `.env`.

### LLM Profiles

Puoi modificare i profili in due modi:

**1. Tramite Dashboard (Consigliato)**
```bash
python dashboard.py
```
Vai su **⚙️ Editor Profili** e modifica i system prompt direttamente dall'interfaccia web.

**2. Manualmente**
Modifica il file `profiles.json`:
```json
{
  "confidential": {
    "system_prompt": "Tuo prompt personalizzato..."
  },
  "formal": {
    "system_prompt": "Tuo prompt personalizzato..."
  },
  "technical": {
    "system_prompt": "Tuo prompt personalizzato..."
  }
}
```

## 🐛 Troubleshooting

### L'overlay non appare
- Verifica che Tkinter sia installato (incluso in Python standard)
- Controlla i messaggi nel terminale per errori

### I pulsanti X e ✓ non sono cliccabili
- **Risolto** nella versione corrente (attributo `-disabled` rimosso)

### Il testo non viene incollato
1. Verifica che l'applicazione target sia in focus quando premi l'hotkey
2. Controlla i messaggi "Focus restored to window" nel terminale
3. Prova ad aumentare il delay in `main.py`:
   ```python
   time.sleep(0.5)  # Prova 0.8 o 1.0
   ```

### Audio di bassa qualità / trascrizioni sbagliate
1. **Controlla il microfono** - Verifica livello input in Windows
2. **Riduci rumore ambientale** - Parla più vicino al microfono
3. **Aggiungi termini** al `personal_dictionary.txt`
4. **Aumenta modello Whisper** a `large` (richiede più VRAM)
5. **Calibrazione** - Il sistema calibra il rumore automaticamente all'avvio

### CUDA non funziona
```bash
python test_cuda.py
```

Se l'errore persiste:
1. Verifica driver NVIDIA aggiornati
2. Reinstalla dipendenze CUDA:
   ```bash
   pip uninstall nvidia-cublas-cu12 nvidia-cudnn-cu12
   pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
   ```

### DeepSeek API errors
- Verifica che `DEEPSEEK_API_KEY` sia corretto in `.env`
- Controlla di avere credito rimanente su [platform.deepseek.com](https://platform.deepseek.com)
- Prova a usare LM Studio invece (locale, nessuna API key necessaria)

## 🔒 Privacy e Sicurezza

### Modalità completamente locale
Per privacy massima, usa **LM Studio** locale:

1. Scarica [LM Studio](https://lmstudio.ai/)
2. Carica un modello (es. Llama-3-8B, Mistral-7B)
3. Avvia server locale
4. Imposta in `.env`:
   ```env
   LLM_PROVIDER=lmstudio
   ```

In questa configurazione:
- ✅ Audio processato localmente su GPU
- ✅ Trascrizione Whisper locale
- ✅ LLM locale (nessuna chiamata cloud)
- ✅ Nessun dato inviato a terze parti

### Modalità cloud (DeepSeek)
Se usi `LLM_PROVIDER=deepseek`:
- ✅ Audio e trascrizione **restano locali**
- ⚠️ Solo il **testo trascritto** viene inviato a DeepSeek API per formattazione
- Più veloce ma meno privato

## 📊 Performance

Benchmark su **RTX 3060 (12GB VRAM)**:

| Fase | Tempo medio |
|------|-------------|
| Registrazione audio | ~5-10s (dipende da quanto parli) |
| Calibrazione VAD | ~0.5s |
| Preprocessing audio | ~0.2s |
| Trascrizione Whisper (medium) | ~2-4s |
| LLM formatting (DeepSeek) | ~1-3s |
| **Totale** | **~8-17s** |

## 🛠️ Sviluppo

### Struttura del codice

- **main.py** - Orchestratore principale, gestione hotkey
- **audio_manager.py** - Registrazione, VAD, preprocessing
- **stt_service.py** - Wrapper faster-whisper
- **llm_service.py** - OpenAI SDK + prompt engineering
- **clipboard_manager.py** - Win32 API clipboard operations
- **recording_indicator.py** - Tkinter UI overlay
- **dashboard.py** - Gradio testing interface

### Testing

Test rapido con dashboard:
```bash
python dashboard.py
```

Test CUDA:
```bash
python test_cuda.py
```

Test completo workflow:
```bash
python main.py
# Premi CTRL+ALT+1 e parla
```

## 🤝 Contribuire

Contributi benvenuti! Per favore:

1. Fork del repository
2. Crea un branch (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📜 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file `LICENSE` per dettagli.

## 🙏 Ringraziamenti

- **Wispr Flow** - Ispirazione originale
- **faster-whisper** - Engine STT performante
- **OpenAI SDK** - Client API per LLM
- **DeepSeek** - API LLM veloce ed economica
- **OpenAI Whisper** - Modello STT di base

## 📞 Supporto

- 🐛 **Issues** - Apri un issue su GitHub
- 💬 **Discussioni** - Usa GitHub Discussions
- 📧 **Email** - [attilio.pregnolato@gmail.com](mailto:attilio.pregnolato@gmail.com)

---

**Fatto con ❤️ in Italia** 🇮🇹
