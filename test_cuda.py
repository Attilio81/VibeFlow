import os
import site

try:
    for site_package in site.getsitepackages():
        for nvidia_pkg in ['cublas', 'cudnn', 'cudnn', 'cufft', 'curand', 'cusolver', 'cusparse', 'nvjitlink']:
            bin_path = os.path.join(site_package, 'nvidia', nvidia_pkg, 'bin')
            if os.path.exists(bin_path):
                print(f"Adding DLL directory: {bin_path}")
                os.add_dll_directory(bin_path)
                os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
except Exception as e:
    print(f"Error adding DLL paths: {e}")

try:
    from faster_whisper import WhisperModel
    print("Faster-whisper imported successfully.")
    import ctranslate2
    print("CTranslate2 CUDA items:", ctranslate2.get_cuda_device_count())
    model = WhisperModel("tiny", device="cuda", compute_type="float16")
    print("CUDA initialization successful!")
except Exception as e:
    print(f"Initialization error: {e}")
