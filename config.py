"""
config.py
Configuration manager for JARVIS AI Assistant.
Loads environment variables from .env and defines runtime constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load .env file
load_dotenv(dotenv_path=ENV_PATH)

# Assistant Identity
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "JARVIS")
USER_NAME = os.getenv("USER_NAME", "Sir")

# AI Brain Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

# Voice Engine Settings
VOICE_RATE = int(os.getenv("JARVIS_VOICE_RATE", "175"))
VOICE_VOLUME = float(os.getenv("JARVIS_VOICE_VOLUME", "1.0"))
VOICE_GENDER = os.getenv("JARVIS_VOICE_GENDER", "male").lower()

# Input Mode: "voice" or "text"
INPUT_MODE = os.getenv("INPUT_MODE", "voice").lower()

# Language Settings
LANG_AUTO = "auto"
LANG_EN = "en"
LANG_HI = "hi"
LANG_HINGLISH = "hinglish"
DEFAULT_LANGUAGE = os.getenv("JARVIS_LANGUAGE", LANG_AUTO).lower()

# Wake Word & Voice Pipeline Settings
WAKE_WORDS = ["hey jarvis", "jarvis", "oye jarvis", "ok jarvis", "namaste jarvis"]
ACTIVATION_CHIME = os.getenv("ACTIVATION_CHIME", "true").lower() == "true"
LISTEN_TIMEOUT_SECONDS = int(os.getenv("LISTEN_TIMEOUT_SECONDS", "8"))

# Assistant State Constants
STATE_IDLE = "IDLE"
STATE_LISTENING = "LISTENING"
STATE_THINKING = "THINKING"
STATE_EXECUTING = "EXECUTING"
STATE_SPEAKING = "SPEAKING"
STATE_ERROR = "ERROR"

# Allowed Safe Directories for File/Folder Operations
ALLOWED_BASE_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    BASE_DIR
]

# Storage Paths
DATABASE_PATH = BASE_DIR / "jarvis_memory.db"
SCREENSHOTS_DIR = BASE_DIR / "Screenshots"
NOTES_DIR = BASE_DIR / "Notes"

# Ensure runtime directories exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)
