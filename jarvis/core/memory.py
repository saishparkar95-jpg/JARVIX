"""
jarvis/core/memory.py
SQLite Database wrapper for storing conversation history, command executions,
controlled long-term memory, reminders, and notes.
"""

import sqlite3
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import config


# Sensitive terms that must NEVER be stored in long-term memory
SENSITIVE_MEMORY_BLOCKLIST = [
    r"password", r"passwd", r"pwd", r"pin\b", r"otp\b",
    r"token", r"secret", r"api[_-]?key", r"credential",
    r"credit\s*card", r"debit\s*card", r"cvv", r"bank\s*account"
]


class MemoryManager:
    """Manages persistent SQLite memory, notes, reminders, and user facts for JARVIS."""

    def __init__(self, db_path=config.DATABASE_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a database connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes database tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Conversation turns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)

            # Command execution log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    command TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT
                )
            """)

            # Controlled Long-Term User Preferences & Facts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at TEXT NOT NULL
                )
            """)
            try:
                cursor.execute("ALTER TABLE user_preferences ADD COLUMN category TEXT DEFAULT 'general'")
            except sqlite3.OperationalError:
                pass

            # Reminders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reminder_text TEXT NOT NULL,
                    target_time TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING', -- PENDING, COMPLETED, CANCELLED
                    created_at TEXT NOT NULL
                )
            """)

            # Notes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # =========================================================================
    # Conversation Logs
    # =========================================================================
    def log_conversation(self, speaker: str, message: str):
        """Records a message in conversation history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (timestamp, speaker, message) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), speaker, message)
            )
            conn.commit()

    def get_recent_conversations(self, limit: int = 6) -> List[Dict[str, str]]:
        """Retrieves recent conversation context."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT speaker, message FROM conversations ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [{"role": "assistant" if row["speaker"] == config.ASSISTANT_NAME else "user", 
                     "content": row["message"]} for row in reversed(rows)]

    def log_action(self, command: str, action_type: str, status: str, details: str = ""):
        """Logs an action executed by JARVIS."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO command_logs (timestamp, command, action_type, status, details) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), command, action_type, status, details)
            )
            conn.commit()

    # =========================================================================
    # Controlled Long-Term Memory (No Passwords or Secrets)
    # =========================================================================
    def set_preference(self, key: str, value: str, category: str = "general") -> bool:
        """
        Saves a user preference or fact.
        Rejects and blocks storing passwords, tokens, API keys, or financial credentials.
        """
        combined = f"{key} {value}".lower()
        for pattern in SENSITIVE_MEMORY_BLOCKLIST:
            if re.search(pattern, combined):
                print(f"[\033[93mMemory Security Alert\033[0m]: Rejected storing sensitive data matching '{pattern}'.")
                return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_preferences (key, value, category, updated_at) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, category=excluded.category, updated_at=excluded.updated_at
                """,
                (key.strip().lower(), value.strip(), category, datetime.now().isoformat())
            )
            conn.commit()
            return True

    def get_preference(self, key: str) -> Optional[str]:
        """Retrieves a specific user preference."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key.strip().lower(),))
            row = cursor.fetchone()
            return row["value"] if row else None

    def get_all_preferences(self) -> List[Dict[str, str]]:
        """Returns all stored harmless user memories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, category, updated_at FROM user_preferences ORDER BY key")
            return [dict(row) for row in cursor.fetchall()]

    def delete_preference(self, key: str) -> bool:
        """Removes a specific memory."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_preferences WHERE key = ?", (key.strip().lower(),))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_memory(self):
        """Clears all long-term user memories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_preferences")
            conn.commit()

    # =========================================================================
    # Reminders System
    # =========================================================================
    def add_reminder(self, reminder_text: str, target_time: datetime) -> int:
        """Adds a new reminder."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (reminder_text, target_time, status, created_at) VALUES (?, ?, 'PENDING', ?)",
                (reminder_text.strip(), target_time.isoformat(), datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid

    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Returns all pending reminders whose target time has arrived or is pending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, reminder_text, target_time FROM reminders WHERE status = 'PENDING' ORDER BY target_time ASC")
            return [dict(row) for row in cursor.fetchall()]

    def mark_reminder_completed(self, reminder_id: int):
        """Marks a reminder as completed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET status = 'COMPLETED' WHERE id = ?", (reminder_id,))
            conn.commit()

    def get_all_reminders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent reminders."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, reminder_text, target_time, status FROM reminders ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_reminder(self, reminder_id: int) -> bool:
        """Deletes a reminder by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0

    # =========================================================================
    # Voice Notes System
    # =========================================================================
    def add_note(self, title: str, content: str) -> int:
        """Saves a new note in database and local Notes folder."""
        created_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (title, content, created_at) VALUES (?, ?, ?)",
                (title.strip(), content.strip(), created_at)
            )
            conn.commit()
            note_id = cursor.lastrowid

        # Also write a text file to Notes/ folder for user convenience
        try:
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or f"note_{note_id}"
            file_path = config.NOTES_DIR / f"{safe_title}.txt"
            file_path.write_text(f"Title: {title}\nDate: {created_at}\n\n{content}", encoding="utf-8")
        except Exception:
            pass

        return note_id

    def get_all_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent notes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, created_at FROM notes ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_note(self, note_id: int) -> bool:
        """Deletes a note by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0
