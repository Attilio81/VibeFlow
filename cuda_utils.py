import os
import site


def add_nvidia_dll_paths() -> None:
    """Add NVIDIA CUDA DLL directories to the PATH so faster-whisper can find them."""
    try:
        packages = site.getsitepackages()
        try:
            user_site = site.getusersitepackages()
            if isinstance(user_site, str):
                packages.append(user_site)
        except Exception:
            pass

        for site_package in packages:
            for nvidia_pkg in ['cublas', 'cudnn', 'cufft', 'curand', 'cusolver', 'cusparse', 'nvjitlink']:
                bin_path = os.path.join(site_package, 'nvidia', nvidia_pkg, 'bin')
                if os.path.exists(bin_path):
                    os.add_dll_directory(bin_path)
                    os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
    except Exception:
        pass
