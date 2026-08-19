"""
jarvis/core/intent_router.py
Comprehensive Intent Router and Natural Language Dispatcher for JARVIS.
Supports Hindi, English, Hinglish, Laptop Controls, Reminders, Notes, Memory, and AI Brain.
"""

import re
from typing import Tuple, Dict, Any
import config
from jarvis.actions.safety import SafetyGuard
from jarvis.actions.system_actions import SystemActions
from jarvis.actions.app_actions import AppActions
from jarvis.actions.web_actions import WebActions
from jarvis.actions.computer_actions import ComputerActions
from jarvis.core.language import LanguageManager
from jarvis.core.context import ContextTracker
from jarvis.core.reminders import ReminderManager


class IntentRouter:
    """Classifies user queries, enforces security rules, handles follow-up context, and routes actions."""

    def __init__(self, memory_manager, ai_brain, tts_engine):
        self.memory = memory_manager
        self.brain = ai_brain
        self.tts = tts_engine
        self.language = LanguageManager(self.memory)
        self.context = ContextTracker()
        self.reminders = ReminderManager(self.memory, self.tts)

    def process_command(self, query: str) -> Tuple[bool, str, bool]:
        """
        Processes a user query.
        Returns: (success: bool, response_message: str, should_exit: bool)
        """
        if not query or not query.strip():
            return False, "", False

        cleaned = query.strip()
        lower = cleaned.lower()
        active_lang = self.language.detect_language(cleaned)

        # ----------------------------------------------------
        # 1. Global Security Check on Raw Command
        # ----------------------------------------------------
        is_safe, safety_msg = SafetyGuard.is_command_safe(cleaned)
        if not is_safe:
            self.memory.log_action(cleaned, "SAFETY_BLOCKED", "BLOCKED", safety_msg)
            return False, safety_msg, False

        # ----------------------------------------------------
        # 2. Language Switch Commands
        # ----------------------------------------------------
        if any(w in lower for w in ["hindi mein baat karo", "speak in hindi", "hindi language"]):
            resp = self.language.set_language("hindi")
            return True, resp, False

        if any(w in lower for w in ["english mein baat karo", "speak in english", "english language"]):
            resp = self.language.set_language("english")
            return True, resp, False

        if any(w in lower for w in ["hinglish mein baat karo", "speak in hinglish", "hinglish language"]):
            resp = self.language.set_language("hinglish")
            return True, resp, False

        # ----------------------------------------------------
        # 3. Exit / Sleep Commands
        # ----------------------------------------------------
        if any(w in lower for w in ["exit", "quit", "goodbye jarvis", "shut down", "band ho jao", "alvida", "sleep"]):
            farewell = "Alvida Sir. Systems shutting down." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else f"Goodbye {config.USER_NAME}. Have a great day."
            self.memory.log_action(cleaned, "SYSTEM_EXIT", "SUCCESS", farewell)
            return True, farewell, True

        # ----------------------------------------------------
        # 4. Laptop Battery & System Telemetry Queries
        # ----------------------------------------------------
        if any(w in lower for w in ["battery kitni hai", "battery percentage", "kitna charge hai", "battery status", "charge kitna hai", "battery kitna hai"]):
            metrics = SystemActions.get_system_metrics()
            bat = metrics["battery"]
            charging = " (Charging)" if metrics["charging"] else ""
            if active_lang in [config.LANG_HI, config.LANG_HINGLISH]:
                resp = f"Aapka laptop {bat} percent charged hai{charging}."
            else:
                resp = f"Your laptop battery is at {bat} percent{charging}, {config.USER_NAME}."
            self.memory.log_action(cleaned, "GET_BATTERY", "SUCCESS", resp)
            return True, resp, False

        if any(w in lower for w in ["cpu kitna hai", "ram kitni use ho rahi hai", "system status", "ram usage", "cpu usage"]):
            metrics = SystemActions.get_system_metrics()
            resp = f"CPU usage is {metrics['cpu']}%, RAM is at {metrics['ram']}%, Network is {metrics['network']}."
            self.memory.log_action(cleaned, "GET_METRICS", "SUCCESS", resp)
            return True, resp, False

        # ----------------------------------------------------
        # 5. Volume & Media Controls
        # ----------------------------------------------------
        vol_pct_match = re.search(r"volume\s+(\d+)\s*(?:percent|%|karo)?", lower)
        if vol_pct_match:
            pct = int(vol_pct_match.group(1))
            success, msg = ComputerActions.set_volume(pct)
            resp = self.language.format_response("VOLUME_SET", f"{pct}%", active_lang)
            return success, resp, False

        if any(w in lower for w in ["volume badhao", "volume up", "increase volume", "aawaz badhao"]):
            ComputerActions.volume_up()
            return True, "Volume badha diya hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else "Volume increased, Sir.", False

        if any(w in lower for w in ["volume kam karo", "volume down", "decrease volume", "aawaz kam karo"]):
            ComputerActions.volume_down()
            return True, "Volume kam kar diya hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else "Volume decreased, Sir.", False

        if any(w in lower for w in ["mute karo", "unmute", "mute system", "aawaz band karo"]):
            ComputerActions.toggle_mute()
            return True, "Mute toggle kar diya hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else "Mute toggled, Sir.", False

        if any(w in lower for w in ["pause music", "play music", "music roko", "gana chalao", "pause media", "play media"]):
            ComputerActions.media_play_pause()
            return True, "Media playback toggled.", False

        if any(w in lower for w in ["lock computer", "computer lock karo", "laptop lock karo", "screen lock karo"]):
            ComputerActions.lock_workstation()
            resp = self.language.format_response("SYSTEM_LOCKED", "", active_lang)
            return True, resp, False

        # ----------------------------------------------------
        # 6. Time & Date Queries
        # ----------------------------------------------------
        if any(w in lower for w in ["what time", "the time", "current time", "kitne baje hain", "kya time hua", "time batao"]):
            time_str = SystemActions.get_current_time()
            self.memory.log_action(cleaned, "GET_TIME", "SUCCESS", time_str)
            return True, time_str, False

        if any(w in lower for w in ["what date", "today's date", "aaj kaun sa din hai", "aaj ki date", "what day is today"]):
            date_str = SystemActions.get_current_date()
            self.memory.log_action(cleaned, "GET_DATE", "SUCCESS", date_str)
            return True, date_str, False

        # ----------------------------------------------------
        # 7. Screenshot Capture
        # ----------------------------------------------------
        if any(w in lower for w in ["take screenshot", "screenshot le lo", "capture screen", "screenshot kheecho", "screenshot"]):
            success, msg = SystemActions.take_screenshot()
            resp = self.language.format_response("TAKE_SCREENSHOT", "", active_lang) if success else msg
            self.memory.log_action(cleaned, "TAKE_SCREENSHOT", "SUCCESS" if success else "FAILED", resp)
            return success, resp, False

        # ----------------------------------------------------
        # 8. Reminders
        # ----------------------------------------------------
        if any(w in lower for w in ["yaad dilana", "remind me", "reminder lagao", "reminder set karo"]):
            success, details = self.reminders.parse_and_create(cleaned)
            resp = self.language.format_response("CREATE_REMINDER", details, active_lang)
            self.memory.log_action(cleaned, "CREATE_REMINDER", "SUCCESS", resp)
            return success, resp, False

        if any(w in lower for w in ["show reminders", "reminders dikhao", "my reminders", "mere reminders"]):
            reminders_list = self.memory.get_all_reminders()
            if not reminders_list:
                return True, "Aapke paas koi pending reminder nahi hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else "You have no active reminders, Sir.", False
            resp = "Your upcoming reminders: " + "; ".join([f"{r['reminder_text']} at {r['target_time']}" for r in reminders_list[:3]])
            return True, resp, False

        # ----------------------------------------------------
        # 9. Voice Notes
        # ----------------------------------------------------
        note_match = re.search(r"(?:note karo|ek note banao|take a note|create a note)[:\s]+(.+)", lower)
        if note_match or ("note" in lower and ("banao" in lower or "write" in lower)):
            content = note_match.group(1).strip() if note_match else cleaned
            self.memory.add_note(title="Voice Note", content=content)
            resp = self.language.format_response("CREATE_NOTE", "", active_lang)
            self.memory.log_action(cleaned, "CREATE_NOTE", "SUCCESS", resp)
            return True, resp, False

        if any(w in lower for w in ["show notes", "mere notes dikhao", "show my notes", "notes dikhao"]):
            notes_list = self.memory.get_all_notes()
            if not notes_list:
                return True, "Aapka koi saved note nahi hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else "You have no saved notes, Sir.", False
            resp = f"Aapke paas {len(notes_list)} notes hain. Latest note: '{notes_list[0]['content']}'"
            return True, resp, False

        # ----------------------------------------------------
        # 10. Long-Term Memory (Remember / Forget)
        # ----------------------------------------------------
        remember_match = re.search(r"(?:remember that|yaad rakhna ki|yaad rakho)\s+(.+)", lower)
        if remember_match:
            fact = remember_match.group(1).strip()
            success = self.memory.set_preference("user_fact", fact, category="facts")
            if success:
                resp = f"Ji {config.USER_NAME}, maine yaad rakh liya hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else f"I will remember that, {config.USER_NAME}."
            else:
                resp = "Security alert: Passwords or private credentials cannot be stored in memory."
            return True, resp, False

        if any(w in lower for w in ["forget that", "clear memory", "ye bhool jao", "memory delete karo"]):
            self.memory.clear_all_memory()
            return True, "Memory clear kar di gayi hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else "Memory has been cleared, Sir.", False

        # ----------------------------------------------------
        # 11. Folder Creation & File Search
        # ----------------------------------------------------
        folder_match = re.search(r"(?:create|make|banao)?(?:\s+a)?\s+folder\s+(?:named|called|naam ka)?\s*([a-zA-Z0-9_\-\s]+)", lower)
        if folder_match and ("folder" in lower or "directory" in lower):
            folder_name = folder_match.group(1).replace("banao", "").replace("karo", "").replace("please", "").strip()
            if folder_name:
                success, msg = SystemActions.create_folder(folder_name, tts_engine=self.tts)
                resp = self.language.format_response("CREATE_FOLDER", folder_name, active_lang) if success else msg
                self.context.update("CREATE_FOLDER", folder_name)
                self.memory.log_action(cleaned, "CREATE_FOLDER", "SUCCESS" if success else "FAILED", resp)
                return success, resp, False

        search_file_match = re.search(r"(?:search file|find file|file dhoondo)\s+([a-zA-Z0-9_\-\.\s]+)", lower)
        if search_file_match:
            file_kw = search_file_match.group(1).strip()
            success, results = ComputerActions.search_files(file_kw)
            return success, f"Found: {', '.join(results)}", False

        # ----------------------------------------------------
        # 12. Web Searches (Google, YouTube, News, Weather)
        # ----------------------------------------------------
        if "weather" in lower or "mausam" in lower:
            loc_match = re.search(r"(?:in|at|ka)\s+([a-zA-Z\s]+)", lower)
            location = loc_match.group(1).strip() if loc_match else ""
            success, query_res = WebActions.search_weather(location)
            return success, f"Showing weather for {query_res}.", False

        if "news" in lower or "khabar" in lower:
            success, query_res = WebActions.search_news()
            return success, f"Showing latest news headlines.", False

        youtube_match = re.search(r"(?:search\s+(?:on\s+)?youtube\s+(?:for\s+)?|youtube\s+par\s+search\s+karo\s+|play\s+)(.+)", lower)
        if youtube_match and "youtube" in lower:
            search_query = youtube_match.group(1).replace("on youtube", "").replace("youtube", "").replace("par", "").replace("search", "").replace("karo", "").strip()
            if search_query:
                success, query_res = WebActions.search_youtube(search_query)
                self.context.update("SEARCH_YOUTUBE", search_query)
                resp = self.language.format_response("SEARCH_YOUTUBE", search_query, active_lang)
                return success, resp, False

        google_match = re.search(r"(?:search\s+(?:for\s+|google\s+for\s+|on\s+google\s+)?|google\s+par\s+search\s+karo\s+|google\s+)(.+)", lower)
        if google_match and ("search" in lower or "google" in lower):
            search_query = google_match.group(1).replace("on google", "").replace("google", "").replace("par", "").replace("search", "").replace("karo", "").strip()
            if search_query:
                success, query_res = WebActions.search_google(search_query)
                self.context.update("SEARCH_WEB", search_query)
                resp = self.language.format_response("SEARCH_WEB", search_query, active_lang)
                return success, resp, False

        # ----------------------------------------------------
        # 13. Close Application (English & Hindi word orders)
        # ----------------------------------------------------
        close_target = None
        if any(w in lower for w in ["close", "band karo", "band kar do", "kill"]):
            # English: "close notepad", Hindi: "notepad band karo"
            close_clean = lower
            for phrase in ["band karo", "band kar do", "band", "close", "kill", "please", "app", "application"]:
                close_clean = close_clean.replace(phrase, "")
            close_target = close_clean.strip()

        if close_target:
            success, msg = ComputerActions.close_app(close_target)
            resp = self.language.format_response("CLOSE_APP", close_target.title(), active_lang) if success else msg
            return success, resp, False

        # ----------------------------------------------------
        # 14. Open Websites or Applications (English & Hindi word orders)
        # ----------------------------------------------------
        open_target = None
        if any(w in lower for w in ["open", "kholo", "khol do", "open karo", "chalao", "launch", "start"]):
            target_clean = lower
            for phrase in ["open karo", "khol do", "khol na", "kholo", "chalao", "launch", "start", "open", "please", "app", "application"]:
                target_clean = target_clean.replace(phrase, "")
            open_target = target_clean.strip()

        if open_target:
            # Check if domain / web shortcut
            if "." in open_target or open_target in ["youtube", "github", "reddit", "google", "wikipedia", "gmail", "netflix", "amazon", "twitter"]:
                success, res_target = WebActions.open_website(open_target)
                self.context.update("OPEN_WEBSITE", open_target)
                return success, f"Opening {open_target} in browser.", False

            # Check if desktop application
            success, app_res = AppActions.open_app(open_target, tts_engine=self.tts)
            if success:
                self.context.update("OPEN_APP", open_target)
                resp = self.language.format_response("OPEN_APP", open_target.title(), active_lang)
                return True, resp, False
            else:
                resp = self.language.format_response("APP_NOT_FOUND", open_target.title(), active_lang)
                return False, resp, False

        # ----------------------------------------------------
        # 15. Follow-up Context Resolution
        # ----------------------------------------------------
        ctx = self.context.get_context()
        if ctx["last_app"] == "chrome" and ("search" in lower or "dhoondo" in lower):
            clean_search = lower.replace("search", "").replace("dhoondo", "").strip()
            if clean_search:
                WebActions.search_google(clean_search)
                return True, f"Searching Google for '{clean_search}'.", False

        # ----------------------------------------------------
        # 16. Fallback to AI Brain (OpenAI / Offline Intelligence)
        # ----------------------------------------------------
        recent_history = self.memory.get_recent_conversations(limit=4)
        ai_response = self.brain.ask(cleaned, conversation_history=recent_history)
        self.memory.log_action(cleaned, "AI_CONVERSATION", "SUCCESS", ai_response)
        return True, ai_response, False
