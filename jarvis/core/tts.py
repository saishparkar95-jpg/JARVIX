"""
jarvis/core/tts.py
Advanced Text-to-Speech engine providing ultra-soft English Neural voice (en-US-AriaNeural)
with instant offline fallback to Microsoft Zira / David and pyttsx3.
"""

import os
import sys
import tempfile
import threading
import ctypes
import asyncio
import pyttsx3
import config

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False


class TTSEngine:
    """Manages Text-to-Speech output with ultra-soft English Neural and offline voice engines."""

    def __init__(self):
        self.lock = threading.Lock()
        self._engine = None
        self._sp_voice = None
        self._use_sp_voice = False
        self._init_engine()

    def _init_engine(self):
        """Initializes offline voice characteristics."""
        try:
            self._engine = pyttsx3.init("sapi5")
            self._engine.setProperty("rate", config.VOICE_RATE)
            self._engine.setProperty("volume", config.VOICE_VOLUME)
            self._apply_voice()
        except Exception as e:
            print(f"[\033[93mWARNING\033[0m] TTS Engine initialization notice: {e}")
            self._engine = None

    def _apply_voice(self):
        """Configures offline English voice based on current config.VOICE_GENDER."""
        target_gender = config.VOICE_GENDER.lower()

        # 1. Try Windows SAPI Desktop Voice Token (Zira / David)
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()

            token_id = (
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
                if target_gender == "female"
                else r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"
            )

            token = win32com.client.Dispatch("SAPI.SpObjectToken")
            token.SetId(token_id)
            self._sp_voice = win32com.client.Dispatch("SAPI.SpVoice")
            self._sp_voice.Voice = token
            self._sp_voice.Rate = 1
            self._sp_voice.Volume = 100
            print(f"\033[92m[English Voice Configured: {self._sp_voice.Voice.GetDescription()}]\033[0m")
            self._use_sp_voice = True
            return
        except Exception:
            self._use_sp_voice = False

        # 2. Fallback to pyttsx3 SAPI5
        if not self._engine:
            return
        try:
            voices = self._engine.getProperty("voices")
            if not voices:
                return

            selected_voice = voices[0]
            if target_gender == "female":
                female_candidates = [
                    v for v in voices
                    if "zira" in v.name.lower()
                    or "female" in getattr(v, "gender", "").lower()
                    or "female" in v.name.lower()
                    or "aria" in v.name.lower()
                    or "eva" in v.name.lower()
                    or "hazel" in v.name.lower()
                ]
                if female_candidates:
                    selected_voice = female_candidates[0]
                elif len(voices) > 1:
                    selected_voice = voices[1]
            else:
                male_candidates = [
                    v for v in voices
                    if "david" in v.name.lower()
                    or "male" in getattr(v, "gender", "").lower()
                    or "male" in v.name.lower()
                    or "george" in v.name.lower()
                ]
                if male_candidates:
                    selected_voice = male_candidates[0]
                else:
                    selected_voice = voices[0]

            self._engine.setProperty("voice", selected_voice.id)
            print(f"\033[90m[TTS Voice Configured: {selected_voice.name}]\033[0m")
        except Exception as e:
            print(f"[\033[93mVoice selection error\033[0m]: {e}")

    def set_gender(self, gender: str) -> str:
        """Dynamically switches between female and male voice."""
        gender = gender.lower()
        if gender not in ["male", "female"]:
            gender = "female"
        config.VOICE_GENDER = gender
        self._apply_voice()
        return f"Voice changed to {gender}."

    def _speak_neural(self, text: str) -> bool:
        """Synthesizes and plays soft, natural English Neural voice (en-US-AriaNeural / en-US-GuyNeural)."""
        if not HAS_EDGE_TTS or not text or not text.strip():
            return False

        target_gender = config.VOICE_GENDER.lower()
        # en-US-AriaNeural is an ultra soft, natural, and expressive English female neural voice
        neural_voice = (
            "en-US-AriaNeural"
            if target_gender == "female"
            else "en-US-GuyNeural"
        )

        temp_audio = os.path.join(tempfile.gettempdir(), f"jarvis_voice_{os.getpid()}_{threading.get_ident()}.mp3")
        try:
            async def _synthesize():
                comm = edge_tts.Communicate(text, neural_voice, rate="+0%", volume="+0%")
                await comm.save(temp_audio)

            asyncio.run(_synthesize())

            if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
                # Play using Windows MCI API
                mci = ctypes.windll.winmm.mciSendStringW
                alias = f"jarvis_tts_{os.getpid()}_{threading.get_ident()}"
                mci(f'open "{temp_audio}" type mpegvideo alias {alias}', None, 0, 0)
                mci(f'play {alias} wait', None, 0, 0)
                mci(f'close {alias}', None, 0, 0)
                return True
        except Exception:
            pass
        finally:
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass
        return False

    def speak(self, text: str):
        """Speaks the text aloud with soft natural voice and prints formatted output."""
        print(f"\n\033[96m[{config.ASSISTANT_NAME}]\033[0m: {text}")

        with self.lock:
            # 1. Primary: Soft Neural English Voice (Studio Quality)
            if self._speak_neural(text):
                return

            # 2. Secondary: Windows SAPI Desktop Voice (Zira / David)
            if getattr(self, "_use_sp_voice", False):
                try:
                    import pythoncom
                    import win32com.client
                    pythoncom.CoInitialize()

                    target_gender = config.VOICE_GENDER.lower()
                    token_id = (
                        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
                        if target_gender == "female"
                        else r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"
                    )
                    token = win32com.client.Dispatch("SAPI.SpObjectToken")
                    token.SetId(token_id)
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Voice = token
                    speaker.Rate = 1
                    speaker.Volume = 100
                    speaker.Speak(text)
                    return
                except Exception as e:
                    print(f"[\033[93mSpVoice notice, falling back\033[0m]: {e}")

            # 3. Offline SAPI5 (pyttsx3)
            if not self._engine:
                return

            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                try:
                    self._init_engine()
                    if self._engine:
                        self._engine.say(text)
                        self._engine.runAndWait()
                except Exception as inner_e:
                    print(f"[\033[91mTTS Error\033[0m]: {inner_e}")
