"""
jarvis/core/context.py
Context manager tracking active application and conversation focus for natural follow-ups.
"""

from typing import Optional, Dict, Any


class ContextTracker:
    """Maintains short-term conversational context across consecutive turns."""

    def __init__(self):
        self.last_intent: Optional[str] = None
        self.last_target: Optional[str] = None
        self.last_app: Optional[str] = None
        self.last_folder: Optional[str] = None

    def update(self, intent: str, target: str = ""):
        """Updates conversational context with most recent action."""
        self.last_intent = intent
        self.last_target = target

        if intent == "OPEN_APP":
            self.last_app = target.lower()
        elif intent in ["CREATE_FOLDER", "OPEN_FOLDER"]:
            self.last_folder = target

    def get_context(self) -> Dict[str, Any]:
        """Returns the current active context snapshot."""
        return {
            "last_intent": self.last_intent,
            "last_target": self.last_target,
            "last_app": self.last_app,
            "last_folder": self.last_folder
        }

    def clear(self):
        """Resets the active context."""
        self.last_intent = None
        self.last_target = None
        self.last_app = None
        self.last_folder = None
