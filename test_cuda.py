from cuda_utils import add_nvidia_dll_paths

add_nvidia_dll_paths()

try:
    from faster_whisper import WhisperModel
    print("Faster-whisper imported successfully.")
    import ctranslate2
    print("CTranslate2 CUDA items:", ctranslate2.get_cuda_device_count())
    model = WhisperModel("tiny", device="cuda", compute_type="float16")
    print("CUDA initialization successful!")
except Exception as e:
    print(f"Initialization error: {e}")
