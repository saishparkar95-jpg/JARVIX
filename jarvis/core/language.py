"""
jarvis/core/language.py
Language Engine: English, Hindi, and Hinglish understanding and natural response generation.
"""

import re
from typing import Tuple, Optional
import config


HINDI_KEYWORDS = [
    r"\bkholo\b", r"\bkhol\b", r"\bband\b", r"\bkaro\b", r"\bkar\b", r"\bdo\b",
    r"\bkitna\b", r"\bkitni\b", r"\bhai\b", r"\bhain\b", r"\bbatao\b", r"\bbataiye\b",
    r"\byaad\b", r"\bdilana\b", r"\bbanao\b", r"\ble\s*lo\b", r"\bkaise\b",
    r"\bkaun\b", r"\bkya\b", r"\bmein\b", r"\bpar\b", r"\bse\b", r"\bmera\b",
    r"\bmeri\b", r"\baap\b", r"\btum\b", r"\bnamaste\b", r"\bdhanyawad\b", r"\bshukriya\b"
]


class LanguageManager:
    """Detects input language, manages user language preference, and generates localized responses."""

    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.current_language = self._load_language_preference()

    def _load_language_preference(self) -> str:
        """Loads stored language preference from SQLite memory."""
        saved = self.memory.get_preference("language")
        if saved in [config.LANG_EN, config.LANG_HI, config.LANG_HINGLISH, config.LANG_AUTO]:
            return saved
        return config.DEFAULT_LANGUAGE

    def set_language(self, lang_code: str) -> str:
        """Updates and persists language mode."""
        clean_code = lang_code.lower().strip()
        if clean_code in ["hindi", "hi", config.LANG_HI]:
            self.current_language = config.LANG_HI
            self.memory.set_preference("language", config.LANG_HI, category="language")
            return "Ab se main aapse Hindi mein baat karunga."
        elif clean_code in ["english", "en", config.LANG_EN]:
            self.current_language = config.LANG_EN
            self.memory.set_preference("language", config.LANG_EN, category="language")
            return "Language switched to English, Sir."
        elif clean_code in ["hinglish", config.LANG_HINGLISH]:
            self.current_language = config.LANG_HINGLISH
            self.memory.set_preference("language", config.LANG_HINGLISH, category="language")
            return "Sure, ab se main Hinglish mein baat karunga."
        else:
            self.current_language = config.LANG_AUTO
            self.memory.set_preference("language", config.LANG_AUTO, category="language")
            return "Automatic language detection enabled."

    def detect_language(self, text: str) -> str:
        """Detects whether text is Hindi, Hinglish, or English based on keywords and script."""
        text_lower = text.lower()
        hindi_count = sum(1 for pattern in HINDI_KEYWORDS if re.search(pattern, text_lower))

        # Check for Devanagari script
        if any('\u0900' <= char <= '\u097F' for char in text):
            return config.LANG_HI

        if hindi_count >= 1:
            return config.LANG_HINGLISH

        return config.LANG_EN

    def format_response(self, intent: str, target: str = "", lang: str = None) -> str:
        """
        Generates natural localized responses based on language preference.
        """
        active_lang = lang or self.current_language
        if active_lang == config.LANG_AUTO:
            active_lang = config.LANG_EN

        responses = {
            "OPEN_APP": {
                config.LANG_HI: f"Ji {config.USER_NAME}, {target} open kar diya hai.",
                config.LANG_HINGLISH: f"Opening {target} for you, {config.USER_NAME}.",
                config.LANG_EN: f"Opening {target} for you, {config.USER_NAME}."
            },
            "CLOSE_APP": {
                config.LANG_HI: f"Ji {config.USER_NAME}, {target} band kar diya hai.",
                config.LANG_HINGLISH: f"Closed {target}, {config.USER_NAME}.",
                config.LANG_EN: f"Closed {target}, {config.USER_NAME}."
            },
            "APP_NOT_FOUND": {
                config.LANG_HI: f"Maaf kijiye, mujhe {target} application nahi mili.",
                config.LANG_HINGLISH: f"Sorry {config.USER_NAME}, I could not find {target}.",
                config.LANG_EN: f"Sorry {config.USER_NAME}, I could not find {target}."
            },
            "SEARCH_WEB": {
                config.LANG_HI: f"Google par {target} search kar raha hoon.",
                config.LANG_HINGLISH: f"Searching Google for '{target}', {config.USER_NAME}.",
                config.LANG_EN: f"Searching Google for '{target}', {config.USER_NAME}."
            },
            "SEARCH_YOUTUBE": {
                config.LANG_HI: f"YouTube par {target} search kar raha hoon.",
                config.LANG_HINGLISH: f"Playing '{target}' on YouTube, {config.USER_NAME}.",
                config.LANG_EN: f"Playing '{target}' on YouTube, {config.USER_NAME}."
            },
            "TAKE_SCREENSHOT": {
                config.LANG_HI: f"Screenshot le liya hai aur save kar diya hai.",
                config.LANG_HINGLISH: f"Screenshot captured and saved, {config.USER_NAME}.",
                config.LANG_EN: f"Screenshot captured and saved, {config.USER_NAME}."
            },
            "CREATE_FOLDER": {
                config.LANG_HI: f"'{target}' folder bana diya hai.",
                config.LANG_HINGLISH: f"Folder '{target}' created successfully.",
                config.LANG_EN: f"Folder '{target}' created successfully."
            },
            "CREATE_NOTE": {
                config.LANG_HI: f"Note save kar liya hai, {config.USER_NAME}.",
                config.LANG_HINGLISH: f"Note saved successfully, {config.USER_NAME}.",
                config.LANG_EN: f"Note saved successfully, {config.USER_NAME}."
            },
            "CREATE_REMINDER": {
                config.LANG_HI: f"Maine '{target}' ka reminder set kar diya hai.",
                config.LANG_HINGLISH: f"Reminder set for '{target}', {config.USER_NAME}.",
                config.LANG_EN: f"Reminder set for '{target}', {config.USER_NAME}."
            },
            "VOLUME_SET": {
                config.LANG_HI: f"Volume {target} percent kar diya hai.",
                config.LANG_HINGLISH: f"Volume set to {target} percent.",
                config.LANG_EN: f"Volume set to {target} percent."
            },
            "SYSTEM_LOCKED": {
                config.LANG_HI: f"Computer lock kar diya hai, {config.USER_NAME}.",
                config.LANG_HINGLISH: f"Computer locked, {config.USER_NAME}.",
                config.LANG_EN: f"Computer locked, {config.USER_NAME}."
            },
            "UNCLEAR": {
                config.LANG_HI: f"Maaf kijiye, mujhe samajh nahi aaya. Kripya dobara boliye.",
                config.LANG_HINGLISH: f"I didn't quite catch that, {config.USER_NAME}. Please say it again.",
                config.LANG_EN: f"I didn't quite catch that, {config.USER_NAME}. Please say it again."
            }
        }

        intent_map = responses.get(intent, {})
        return intent_map.get(active_lang, intent_map.get(config.LANG_EN, f"Action completed for {target}."))
