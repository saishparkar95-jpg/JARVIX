"""
jarvis/core/wake_word.py
Local wake-word detector and activation chime engine for JARVIS.
"""

import sys
import re
from typing import Tuple, Optional
import config

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class WakeWordDetector:
    """Manages wake-word recognition, inline query extraction, and activation sounds."""

    def __init__(self, wake_words=None):
        self.wake_words = wake_words or config.WAKE_WORDS

    def play_activation_sound(self):
        """Plays a pleasant, short ascending two-tone chime upon wake-word activation."""
        if not config.ACTIVATION_CHIME or not HAS_WINSOUND:
            return

        try:
            # Ascending dual-tone notification chime (Google Assistant style)
            winsound.Beep(1000, 90)
            winsound.Beep(1500, 120)
        except Exception:
            pass

    def check_wake_word(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if the query contains a wake word.
        Returns:
            (has_wake_word: bool, remaining_command: Optional[str])
            - If user said "Hey Jarvis what is the time" -> (True, "what is the time")
            - If user said "Hey Jarvis" -> (True, None)
            - If user said "What is the time" -> (False, None)
        """
        if not query or not query.strip():
            return False, None

        cleaned = query.strip().lower()

        for wake_word in self.wake_words:
            # Check exact match: "hey jarvis"
            if cleaned == wake_word:
                return True, None

            # Check starts with wake word: "hey jarvis open chrome"
            pattern = rf"^\b{re.escape(wake_word)}\b[\s,:]*(.*)"
            match = re.match(pattern, cleaned)
            if match:
                remaining = match.group(1).strip()
                return True, remaining if remaining else None

            # Check if wake word is anywhere in text
            if wake_word in cleaned:
                # Remove the wake word and return the rest
                remainder = cleaned.replace(wake_word, "").strip()
                remainder = re.sub(r"^[\s,:]+", "", remainder)
                return True, remainder if remainder else None

        return False, None
