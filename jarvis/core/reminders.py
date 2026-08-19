"""
jarvis/core/reminders.py
Local reminder parser and background scheduler engine using SQLite memory.
"""

import re
import time
import threading
from datetime import datetime, timedelta
from typing import Tuple, Optional
import config


class ReminderManager:
    """Manages reminder parsing, storage, and background notification triggers."""

    def __init__(self, memory_manager, tts_engine=None):
        self.memory = memory_manager
        self.tts = tts_engine
        self.is_running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self._thread.start()

    def parse_and_create(self, query: str) -> Tuple[bool, str]:
        """
        Parses voice / text query for reminder details and target time.
        Supports Hindi, English, and Hinglish syntax.
        """
        query_lower = query.lower()

        # Extract text: e.g. "mujhe 8 baje medicine yaad dilana" -> "medicine"
        # Extract time: e.g. "in 10 minutes", "at 7 pm", "8 baje"
        target_time = None
        reminder_text = ""

        # Check "in X minutes / seconds / hours"
        relative_match = re.search(r"in\s+(\d+)\s+(minute|min|hour|hr|second|sec)s?", query_lower)
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2)
            if "sec" in unit:
                target_time = datetime.now() + timedelta(seconds=amount)
            elif "min" in unit:
                target_time = datetime.now() + timedelta(minutes=amount)
            elif "hour" in unit or "hr" in unit:
                target_time = datetime.now() + timedelta(hours=amount)

            # Strip time part to get reminder text
            reminder_text = re.sub(r"(?:remind me|yaad dilana|set a reminder)\s+(?:to\s+)?", "", query_lower)
            reminder_text = re.sub(r"in\s+\d+\s+\w+", "", reminder_text).strip()

        # Check "at X pm / am" or "X baje"
        if not target_time:
            time_match = re.search(r"(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje)?", query_lower)
            if time_match and ("remind" in query_lower or "yaad" in query_lower):
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)

                if meridiem == "pm" and hour < 12:
                    hour += 12
                elif meridiem == "am" and hour == 12:
                    hour = 0
                elif meridiem == "baje" and hour < 8:
                    # Default afternoon/evening assumption for common hours
                    hour += 12

                now = datetime.now()
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target_time <= now:
                    target_time += timedelta(days=1)  # Next day

                reminder_text = re.sub(r"(?:remind me|mujhe|yaad dilana|set reminder)\s+(?:to\s+)?", "", query_lower)
                reminder_text = re.sub(r"\d{1,2}(?::\d{2})?\s*(?:am|pm|baje)?", "", reminder_text).strip()

        if not target_time:
            # Default fallback: 30 minutes from now
            target_time = datetime.now() + timedelta(minutes=30)
            reminder_text = query_lower.replace("remind me", "").replace("yaad dilana", "").strip()

        clean_text = reminder_text if reminder_text else "your scheduled task"
        self.memory.add_reminder(clean_text, target_time)

        time_formatted = target_time.strftime("%I:%M %p")
        return True, f"'{clean_text}' at {time_formatted}"

    def _daemon_loop(self):
        """Monitors database for pending reminders in the background."""
        while self.is_running:
            try:
                now = datetime.now().isoformat()
                pending = self.memory.get_pending_reminders()
                for r in pending:
                    if r["target_time"] <= now:
                        reminder_id = r["id"]
                        text = r["reminder_text"]
                        self.memory.mark_reminder_completed(reminder_id)

                        msg = f"{config.USER_NAME}, aapne '{text}' ka reminder set kiya tha."
                        print(f"\n\033[93m[🔔 REMINDER ALERT]\033[0m: {msg}")
                        if self.tts:
                            self.tts.speak(msg)
            except Exception:
                pass
            time.sleep(10)

    def stop(self):
        self.is_running = False
