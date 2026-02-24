import sounddevice as sd
import soundfile as sf
import numpy as np
import winsound
import time
import threading
import noisereduce as nr
from scipy import signal

class AudioManager:
    def __init__(self):
        # Optimal settings for Whisper
        self.sample_rate = 16000  # Whisper's native sample rate
        self.channels = 1  # Mono for better STT
        self.dtype = 'int16'  # 16-bit PCM
        
        # Voice Activity Detection parameters
        self.silence_threshold = 0.015  # RMS threshold for silence detection (increased sensitivity)
        self.silence_duration = 3.0  # Seconds of silence before stopping (more time to think)
        self.max_duration = 60  # Maximum recording duration in seconds
        self.min_duration = 0.3  # Minimum speech duration to be valid
        
        # External control
        self.stop_callback = None  # Callback to check if user requested stop

    def play_sound(self, sound_type: str):
        """Plays a system beep to indicate status."""
        def _play():
            if sound_type == "start":
                # High beep for start
                winsound.Beep(1000, 200)
            elif sound_type == "processing":
                # Two quick beeps
                winsound.Beep(800, 100)
                time.sleep(0.05)
                winsound.Beep(800, 100)
            elif sound_type == "success":
                # Ascending beeps
                winsound.Beep(600, 150)
                time.sleep(0.05)
                winsound.Beep(900, 200)
        
        threading.Thread(target=_play, daemon=True).start()

    def calculate_rms(self, audio_chunk):
        """Calculate Root Mean Square (RMS) energy of audio chunk."""
        return np.sqrt(np.mean(audio_chunk.astype(float)**2))
    
    def preprocess_audio(self, audio_data):
        """Apply balanced noise reduction and normalization for better STT."""
        # Convert to float for processing
        audio_float = audio_data.astype(np.float32).flatten()
        
        # 1. Moderate noise reduction (not too aggressive)
        audio_float = nr.reduce_noise(
            y=audio_float, 
            sr=self.sample_rate, 
            stationary=True,
            prop_decrease=0.8  # Moderate reduction
        )
        
        # 2. High-pass filter to remove low-frequency rumble (< 80 Hz)
        sos_hp = signal.butter(3, 80, 'hp', fs=self.sample_rate, output='sos')
        audio_float = signal.sosfilt(sos_hp, audio_float)
        
        # 3. Low-pass filter to remove high-frequency noise (> 7500 Hz)
        sos_lp = signal.butter(3, 7500, 'lp', fs=self.sample_rate, output='sos')
        audio_float = signal.sosfilt(sos_lp, audio_float)
        
        # 4. Simple normalization to -1 dB
        max_val = np.abs(audio_float).max()
        if max_val > 0:
            target_level = 0.891  # -1 dB
            audio_float = audio_float * (target_level / max_val)
        
        # 5. Convert back to int16
        audio_int16 = np.clip(audio_float * 32767, -32768, 32767).astype(np.int16)
        
        return audio_int16.reshape(-1, 1)

    def record_audio(self, stop_callback=None) -> str | None:
        """Records from the microphone with VAD until silence or manual stop, returns wav file path.
        
        Args:
            stop_callback: Optional function that returns True when user wants to stop recording
        """
        temp_file = "temp_audio.wav"
        self.stop_callback = stop_callback
        
        print("Calibrating noise level...")
        # Record 0.5 seconds to calibrate noise threshold
        calibration = sd.rec(int(0.5 * self.sample_rate), 
                            samplerate=self.sample_rate, 
                            channels=self.channels, 
                            dtype=self.dtype)
        sd.wait()
        noise_level = self.calculate_rms(calibration)
        # Set threshold above noise level
        self.silence_threshold = max(noise_level * 2.5, 0.01)
        
        self.play_sound("start")
        print(f"Listening... (silence threshold: {self.silence_threshold:.4f})")
        print("Click STOP button or wait for silence detection to end recording")
        
        # Start recording
        recording = []
        silence_duration_counter = 0
        speech_detected = False
        chunk_duration = 0.1  # Process in 100ms chunks
        chunk_size = int(chunk_duration * self.sample_rate)
        
        try:
            stream = sd.InputStream(samplerate=self.sample_rate, 
                                   channels=self.channels, 
                                   dtype=self.dtype)
            stream.start()
            
            total_duration = 0
            
            while total_duration < self.max_duration:
                # Check if user clicked stop button
                if self.stop_callback and self.stop_callback():
                    print("Manual stop requested by user")
                    break
                
                # Read a chunk
                chunk, overflowed = stream.read(chunk_size)
                recording.append(chunk)
                
                # Calculate energy
                rms = self.calculate_rms(chunk)
                
                # Check if speech is detected
                if rms > self.silence_threshold:
                    speech_detected = True
                    silence_duration_counter = 0
                elif speech_detected:
                    # We had speech, now silence
                    silence_duration_counter += chunk_duration
                    
                    if silence_duration_counter >= self.silence_duration:
                        print(f"Silence detected for {self.silence_duration}s, stopping...")
                        break
                
                total_duration += chunk_duration
            
            stream.stop()
            stream.close()
            
            # Check if we got valid speech
            if not speech_detected:
                print("No speech detected.")
                return None
            
            if total_duration < self.min_duration:
                print("Recording too short.")
                return None
            
            # Combine all chunks
            audio_data = np.concatenate(recording, axis=0)
            
            self.play_sound("processing")
            
            # Apply audio preprocessing for better STT accuracy
            audio_data = self.preprocess_audio(audio_data)
            
            # Save as WAV file
            sf.write(temp_file, audio_data, self.sample_rate)
            print(f"Recorded {total_duration:.1f}s of audio (preprocessed)")
            
            return temp_file
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None
