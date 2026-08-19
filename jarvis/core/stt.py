"""
jarvis/core/stt.py
Continuous Real-Time Streaming Speech-to-Text engine.
Functions like Google Assistant / Alexa with continuous listening, ring buffer, and zero button clicks needed.
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
    """Continuous stream audio capture and speech recognition engine."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.sample_rate = 16000
        self.chunk_duration = 0.05  # 50ms chunks for instant responsiveness
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)

        # Pre-roll buffer (0.4s) to capture the start of speech without clipping
        self.pre_buffer = collections.deque(maxlen=8)
        self.stream = None
        self.is_active = True
        self.microphone_available = self._check_microphone()

        if self.microphone_available and HAS_SOUNDDEVICE:
            self._start_stream()

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
        """Starts a persistent, low-latency audio input stream."""
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

    def listen_continuous(self, silence_threshold=0.006, max_duration=10, silence_limit=1.1) -> str:
        """
        Continuously reads the live audio stream.
        Triggers automatically when user speaks (like Google Assistant) without pressing any buttons.
        """
        if config.INPUT_MODE == "text" or not self.stream:
            return self._listen_text()

        frames = []
        started_speaking = False
        silence_time = 0.0
        start_time = time.time()

        # Restart stream if closed
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
                    # Keep rolling pre-buffer
                    self.pre_buffer.append(audio_data)

                    # Trigger as soon as voice energy is detected
                    if energy > silence_threshold:
                        started_speaking = True
                        frames.extend(list(self.pre_buffer))
                        frames.append(audio_data)
                        silence_time = 0.0
                        start_time = time.time()
                else:
                    frames.append(audio_data)
                    if energy < silence_threshold:
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

    def _transcribe(self, wav_bytes: bytes) -> str:
        """Transcribes audio using Google Speech API with Indian accent & Hindi support."""
        if not wav_bytes:
            return ""
        try:
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio = self.recognizer.record(source)

            # Try en-IN first (recognizes Indian English, Hinglish, and tech keywords accurately)
            try:
                text = self.recognizer.recognize_google(audio, language="en-IN")
                return text.strip()
            except sr.UnknownValueError:
                # Fallback to Hindi
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
