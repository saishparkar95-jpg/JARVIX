"""
jarvis/core/tts.py
Offline Text-to-Speech engine utilizing Windows SAPI5 via pyttsx3.
"""

import threading
import pyttsx3
import config


class TTSEngine:
    """Manages Text-to-Speech output for JARVIS."""

    def __init__(self):
        self.lock = threading.Lock()
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        """Initializes the pyttsx3 engine and configures voice characteristics."""
        try:
            self._engine = pyttsx3.init("sapi5")
            self._engine.setProperty("rate", config.VOICE_RATE)
            self._engine.setProperty("volume", config.VOICE_VOLUME)

            voices = self._engine.getProperty("voices")
            if voices:
                # Select voice matching configuration (male / female preference)
                selected_voice = voices[0]
                if config.VOICE_GENDER == "female" and len(voices) > 1:
                    selected_voice = voices[1]
                self._engine.setProperty("voice", selected_voice.id)
        except Exception as e:
            print(f"[\033[93mWARNING\033[0m] TTS Engine initialization notice: {e}")
            self._engine = None

    def speak(self, text: str):
        """Speaks the text aloud and prints formatted output in the console."""
        print(f"\n\033[96m[{config.ASSISTANT_NAME}]\033[0m: {text}")

        if not self._engine:
            return

        with self.lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                # Fallback to re-initialize if COM connection closed
                try:
                    self._init_engine()
                    if self._engine:
                        self._engine.say(text)
                        self._engine.runAndWait()
                except Exception as inner_e:
                    print(f"[\033[91mTTS Error\033[0m]: {inner_e}")
