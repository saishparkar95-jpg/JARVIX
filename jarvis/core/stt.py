"""
jarvis/core/stt.py
Adaptive real-time Speech-to-Text engine with auto-calibrated noise floor.
"""

import io
import time
import wave
import collections
from typing import Tuple, Optional
import numpy as np
import speech_recognition as sr
import config

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


class STTEngine:
    """Continuous stream audio capture and speech recognition engine with adaptive noise floor."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.sample_rate = 16000
        self.chunk_duration = 0.05
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)

        self.pre_buffer = collections.deque(maxlen=10)
        self.stream = None
        self.is_active = True
        self.ambient_energy = 0.005
        self.speech_threshold = 0.012

        self.microphone_available = self._check_microphone()
        if self.microphone_available and HAS_SOUNDDEVICE:
            self._start_stream()
            self._calibrate_ambient_noise()

    def _check_microphone(self) -> bool:
        """Verifies if microphone hardware is accessible."""
        if HAS_SOUNDDEVICE:
            try:
                devices = sd.query_devices()
                input_devs = [d for d in devices if d.get('max_input_channels', 0) > 0]
                if input_devs:
                    return True
            except Exception:
                pass
        return False

    def _start_stream(self):
        """Starts a persistent low-latency audio input stream."""
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.chunk_samples
            )
            self.stream.start()
        except Exception as e:
            print(f"[\033[93mStream notice\033[0m]: {e}")
            self.stream = None

    def _calibrate_ambient_noise(self):
        """Measures ambient room sound for 0.4s to set adaptive sensitivity."""
        if not self.stream:
            return
        energies = []
        for _ in range(8):
            try:
                chunk, _ = self.stream.read(self.chunk_samples)
                audio_data = chunk[:, 0]
                energies.append(float(np.sqrt(np.mean(audio_data**2))))
            except Exception:
                pass
        if energies:
            self.ambient_energy = max(0.002, float(np.mean(energies)))
            # Adaptive threshold: 2.2x ambient noise floor, clamped between 0.010 and 0.040
            self.speech_threshold = max(0.010, min(0.040, self.ambient_energy * 2.2))
            print(f"\033[90m[Microphone Calibrated: Ambient={self.ambient_energy:.4f}, Threshold={self.speech_threshold:.4f}]\033[0m")

    def listen_continuous(self, max_duration=8, silence_limit=0.55, silence_threshold: Optional[float] = None, **kwargs) -> str:
        """
        Continuously reads the live audio stream with adaptive noise detection.
        Triggers automatically when voice is spoken.
        """
        if config.INPUT_MODE == "text" or not self.stream:
            return self._listen_text()

        frames = []
        started_speaking = False
        silence_time = 0.0
        start_time = time.time()
        effective_threshold = silence_threshold if silence_threshold is not None else self.speech_threshold

        if not self.stream.active:
            try:
                self.stream.start()
            except Exception:
                self._start_stream()

        while self.is_active:
            try:
                chunk, overflow = self.stream.read(self.chunk_samples)
                audio_data = chunk[:, 0]
                energy = float(np.sqrt(np.mean(audio_data**2)))

                if not started_speaking:
                    self.pre_buffer.append(audio_data)

                    # Speech detected
                    if energy > effective_threshold:
                        started_speaking = True
                        frames.extend(list(self.pre_buffer))
                        frames.append(audio_data)
                        silence_time = 0.0
                        start_time = time.time()
                else:
                    frames.append(audio_data)
                    # Use lower threshold to detect pause / silence
                    if energy < (effective_threshold * 0.75):
                        silence_time += self.chunk_duration
                        if silence_time >= silence_limit:
                            break
                    else:
                        silence_time = 0.0

                    if (time.time() - start_time) >= max_duration:
                        break

            except Exception:
                time.sleep(0.05)

        if not started_speaking or not frames:
            return ""

        # Convert to WAV
        full_audio = np.concatenate(frames)
        int_audio = (full_audio * 32767).astype(np.int16)

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(int_audio.tobytes())

        wav_io.seek(0)
        return self._transcribe(wav_io.read())

    def listen_for_wake_word(self, wake_detector=None) -> Tuple[bool, Optional[str]]:
        """Listens for wake words (compatible with CLI assistant)."""
        text = self.listen_continuous()
        if not text:
            return False, None
        if wake_detector:
            return wake_detector.check_wake_word(text)
        return True, text

    def listen_command(self, max_duration: int = 9) -> str:
        """Listens for a user command after activation (compatible with CLI assistant)."""
        return self.listen_continuous(max_duration=max_duration)

    def _transcribe(self, wav_bytes: bytes) -> str:
        """Transcribes audio using Google Speech API with Indian accent & Hindi support."""
        if not wav_bytes:
            return ""
        try:
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio = self.recognizer.record(source)

            # Try en-IN first
            try:
                text = self.recognizer.recognize_google(audio, language="en-IN")
                return text.strip()
            except sr.UnknownValueError:
                # Fallback to hi-IN
                try:
                    text = self.recognizer.recognize_google(audio, language="hi-IN")
                    return text.strip()
                except Exception:
                    return ""

        except Exception:
            return ""

    def _listen_text(self) -> str:
        """Console input fallback."""
        try:
            query = input(f"\n\033[94m[{config.USER_NAME} (Text)]\033[0m: ")
            return query.strip()
        except (KeyboardInterrupt, EOFError):
            return "exit"

    def close(self):
        """Closes audio stream cleanly."""
        self.is_active = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
