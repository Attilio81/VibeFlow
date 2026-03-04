import sounddevice as sd
import soundfile as sf
import numpy as np
import winsound
import time
import tempfile
import threading
import logging
import queue
import webrtcvad

logger = logging.getLogger("vibeflow")


class AudioManager:
    def __init__(self):
        # Optimal settings for Whisper
        self.sample_rate = 16000  # Whisper's native sample rate
        self.channels = 1  # Mono for better STT
        self.dtype = 'int16'  # 16-bit PCM

        # Voice Activity Detection parameters
        self.vad = webrtcvad.Vad(3)  # Aggressiveness from 0 to 3
        
        # WebRTC VAD needs 10, 20, or 30 ms frames. 
        self.frame_duration_ms = 30
        self.frame_size = int(self.sample_rate * (self.frame_duration_ms / 1000.0)) # 480 samples

        self.silence_duration = 5.0  # Seconds of silence before stopping
        self.max_duration = 60  # Maximum recording duration in seconds
        self.min_duration = 0.3  # Minimum speech duration to be valid
        
        self.audio_queue = queue.Queue()

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

    def record_audio(self, stop_callback=None, audio_level_callback=None) -> str | None:
        """Records from the microphone with VAD until silence or manual stop.

        Args:
            stop_callback: Optional function that returns True when user wants to stop recording.
            audio_level_callback: Optional function called with the current RMS level (float)
                for each audio chunk, used to drive the waveform visualiser.

        Returns:
            Path to a temporary WAV file, or None if no valid speech was captured.
            The caller (STTService) is responsible for deleting the file after use.
        """
        self.stop_callback = stop_callback

        self.play_sound("start")
        logger.info("Listening... waiting for speech")
        logger.info("Click STOP button or wait for silence detection to end recording")

        recording = []
        silence_duration_counter = 0.0
        speech_detected = False
        
        # Clear the queue from any previous runs
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

        # Buffer to accumulate incoming audio samples until we have a full VAD frame
        sample_buffer = np.array([], dtype=np.int16)

        def audio_callback(indata, frames, time_info, status):
            """Callback for sounddevice. Puts audio chunks into the queue asynchronously."""
            if status:
                logger.warning(f"SoundDevice status: {status}")
            self.audio_queue.put(indata.copy())

        # Use a unique temp file per recording to avoid collisions
        tmp_fd, temp_file = tempfile.mkstemp(suffix=".wav", prefix="vibeflow_")

        try:
            stream = sd.InputStream(samplerate=self.sample_rate,
                                   channels=self.channels,
                                   dtype=self.dtype,
                                   callback=audio_callback)
            
            with stream:
                total_duration = 0.0
                start_time = time.time()
                
                while total_duration < self.max_duration:
                    # Check if user clicked stop button
                    if self.stop_callback and self.stop_callback():
                        logger.info("Manual stop requested by user")
                        break

                    try:
                        # Wait for a chunk from the callback thread
                        chunk = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                        
                    recording.append(chunk)
                    
                    # Flatten the chunk to 1D and append to buffer
                    flat_chunk = chunk.flatten()
                    sample_buffer = np.append(sample_buffer, flat_chunk)

                    # Update UI waveform if a callback is provided (calculate rough RMS)
                    if audio_level_callback:
                        rms = np.sqrt(np.mean(flat_chunk.astype(float)**2)) if len(flat_chunk) > 0 else 0
                        audio_level_callback(rms)

                    # Process buffer in chunks of `frame_size` for WebRTC VAD
                    while len(sample_buffer) >= self.frame_size:
                        # Extract one frame
                        frame = sample_buffer[:self.frame_size]
                        # Remove it from buffer
                        sample_buffer = sample_buffer[self.frame_size:]
                        
                        # Convert to bytes for WebRTC VAD
                        frame_bytes = frame.tobytes()
                        
                        try:
                            is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                        except Exception as e:
                            logger.error(f"VAD error: {e}")
                            is_speech = False
                            
                        # Keep track of silence
                        if is_speech:
                            speech_detected = True
                            silence_duration_counter = 0.0
                        elif speech_detected:
                            # We had speech, now silence
                            silence_duration_counter += (self.frame_duration_ms / 1000.0)

                    if speech_detected and silence_duration_counter >= self.silence_duration:
                        logger.info(f"Silence detected for {self.silence_duration}s, stopping...")
                        break
                        
                    total_duration = time.time() - start_time

            # Reset level indicator to zero when recording ends
            if audio_level_callback:
                audio_level_callback(0.0)

            # Check if we got valid speech
            if not speech_detected:
                logger.warning("No speech detected.")
                return None

            if total_duration < self.min_duration:
                logger.warning("Recording too short.")
                return None

            # Combine all chunks
            audio_data = np.concatenate(recording, axis=0)

            self.play_sound("processing")

            # Write to the temp file (fd is already open – close it first so sf can write)
            import os
            os.close(tmp_fd)
            sf.write(temp_file, audio_data, self.sample_rate)
            logger.info(f"Recorded {total_duration:.1f}s of audio → {temp_file}")

            return temp_file

        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            # Clean up temp file on failure
            try:
                import os
                os.close(tmp_fd)
            except Exception:
                pass
            try:
                import os
                os.unlink(temp_file)
            except Exception:
                pass
            return None
