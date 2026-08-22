"""
jarvis/core/intent_router.py
Comprehensive Intent Router and Natural Language Dispatcher for JARVIS.
Supports Hindi, English, Hinglish, Windows Control, File Operations, Multi-Step Tasks,
Safety Permission Levels, Reminders, Notes, Memory, and AI Brain.
"""

import re
from pathlib import Path
import pyperclip
from typing import Tuple, Dict, Any, Optional
import config
from jarvis.core.security_manager import SecurityManager, PermissionLevel
from jarvis.actions.safety import SafetyGuard
from jarvis.actions.system_actions import SystemActions
from jarvis.actions.app_actions import AppActions
from jarvis.actions.web_actions import WebActions
from jarvis.actions.computer_actions import ComputerActions
from jarvis.actions.file_actions import FileActions
from jarvis.actions.window_actions import WindowActions
from jarvis.actions.power_actions import PowerActions
from jarvis.core.planner import TaskPlanner
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
        self.planner = TaskPlanner(self.memory, self.tts)
        self.last_search_results = []

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
        # 1. Global Security Validation
        # ----------------------------------------------------
        is_safe, safety_msg = SafetyGuard.is_command_safe(cleaned)
        if not is_safe:
            self.memory.log_action(cleaned, "SAFETY_BLOCKED", "BLOCKED", safety_msg)
            return False, safety_msg, False

        # ----------------------------------------------------
        # 2. Emergency Stop
        # ----------------------------------------------------
        if any(w in lower for w in ["jarvis stop", "stop jarvis", "emergency stop", "cancel all"]):
            PowerActions.cancel_shutdown()
            return True, f"All operations stopped immediately, {config.USER_NAME}.", False

        # ----------------------------------------------------
        # 3. Multi-Step Task Execution Planner
        # ----------------------------------------------------
        if self.planner.is_multi_step_request(cleaned):
            success, plan_resp = self.planner.plan_and_execute(cleaned)
            self.memory.log_action(cleaned, "MULTI_STEP_PLAN", "SUCCESS" if success else "FAILED", plan_resp)
            return success, plan_resp, False

        # ----------------------------------------------------
        # 4. Language & Voice Settings
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

        if any(w in lower for w in ["female voice", "ladki ki aawaz", "change voice to female", "switch to female voice", "set voice female"]):
            if hasattr(self.tts, "set_gender"):
                self.tts.set_gender("female")
            resp = "Maine female voice activate kar di hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else f"Female voice activated, {config.USER_NAME}."
            return True, resp, False

        if any(w in lower for w in ["male voice", "ladke ki aawaz", "change voice to male", "switch to male voice", "set voice male"]):
            if hasattr(self.tts, "set_gender"):
                self.tts.set_gender("male")
            resp = "Maine male voice activate kar di hai." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else f"Male voice activated, {config.USER_NAME}."
            return True, resp, False

        # ----------------------------------------------------
        # 5. Exit Commands
        # ----------------------------------------------------
        if any(w in lower for w in ["exit", "quit", "goodbye jarvis", "band ho jao", "alvida", "close jarvis"]):
            farewell = "Alvida Sir. Systems shutting down." if active_lang in [config.LANG_HI, config.LANG_HINGLISH] else f"Goodbye {config.USER_NAME}. Have a great day."
            self.memory.log_action(cleaned, "SYSTEM_EXIT", "SUCCESS", farewell)
            return True, farewell, True

        # ----------------------------------------------------
        # 6. Power & System Controls (With Level 2 Confirmation)
        # ----------------------------------------------------
        if any(w in lower for w in ["cancel shutdown", "abort shutdown", "shutdown cancel karo"]):
            success, msg = PowerActions.cancel_shutdown()
            return success, msg, False

        if any(w in lower for w in ["shut down the laptop", "shut down my laptop", "shutdown laptop", "shutdown computer", "turn off laptop", "turn off computer"]):
            action_desc = "shut down the Windows computer"
            confirmed = SafetyGuard.request_confirmation(action_desc, tts_engine=self.tts)
            if confirmed:
                success, msg = PowerActions.shutdown_laptop(confirmed=True, delay_seconds=20)
                return success, msg, False
            return False, "Shutdown cancelled by user.", False

        if any(w in lower for w in ["restart the laptop", "restart my laptop", "restart laptop", "restart computer", "reboot laptop"]):
            action_desc = "restart the Windows computer"
            confirmed = SafetyGuard.request_confirmation(action_desc, tts_engine=self.tts)
            if confirmed:
                success, msg = PowerActions.restart_laptop(confirmed=True, delay_seconds=20)
                return success, msg, False
            return False, "Restart cancelled by user.", False

        if any(w in lower for w in ["sleep the laptop", "put laptop to sleep", "sleep computer"]):
            action_desc = "put the computer to sleep"
            confirmed = SafetyGuard.request_confirmation(action_desc, tts_engine=self.tts)
            if confirmed:
                success, msg = PowerActions.sleep_laptop(confirmed=True)
                return success, msg, False
            return False, "Sleep mode cancelled by user.", False

        if any(w in lower for w in ["lock computer", "computer lock karo", "laptop lock karo", "screen lock karo", "lock my laptop", "lock the laptop"]):
            PowerActions.lock_workstation()
            resp = self.language.format_response("SYSTEM_LOCKED", "", active_lang)
            return True, resp, False

        # ----------------------------------------------------
        # 7. System Telemetry (Battery, RAM, CPU, Storage, Network)
        # ----------------------------------------------------
        if any(w in lower for w in ["battery kitni hai", "battery percentage", "kitna charge hai", "battery status", "show me my battery", "how much battery", "is my laptop charging"]):
            metrics = SystemActions.get_system_metrics()
            bat = metrics["battery"]
            charging = " (Charging)" if metrics["charging"] else ""
            resp = f"Your laptop battery is at {bat} percent{charging}, {config.USER_NAME}."
            self.memory.log_action(cleaned, "GET_BATTERY", "SUCCESS", resp)
            return True, resp, False

        if any(w in lower for w in ["how much ram", "ram usage", "ram kitni use", "tell me how much ram"]):
            metrics = SystemActions.get_system_metrics()
            resp = f"You are currently using {metrics['ram']}% of RAM, {config.USER_NAME}."
            return True, resp, False

        if any(w in lower for w in ["cpu usage", "what cpu", "cpu kitna hai"]):
            metrics = SystemActions.get_system_metrics()
            resp = f"Current CPU utilization is {metrics['cpu']}%, {config.USER_NAME}."
            return True, resp, False

        if any(w in lower for w in ["system status", "laptop status", "telemetry"]):
            metrics = SystemActions.get_system_metrics()
            resp = f"CPU: {metrics['cpu']}%, RAM: {metrics['ram']}%, Battery: {metrics['battery']}%, Network: {metrics['network']}."
            return True, resp, False

        if any(w in lower for w in ["what time", "current time", "kitne baje hain", "kya time hua", "time batao"]):
            time_str = SystemActions.get_current_time()
            return True, time_str, False

        if any(w in lower for w in ["what date", "today's date", "aaj kaun sa din hai", "aaj ki date", "what day is today"]):
            date_str = SystemActions.get_current_date()
            return True, date_str, False

        # ----------------------------------------------------
        # 8. Volume & Media Controls
        # ----------------------------------------------------
        vol_pct_match = re.search(r"(?:volume\s+(?:to\s+)?(\d+)|increase\s+the\s+volume\s+to\s+(\d+)|set\s+volume\s+(?:to\s+)?(\d+))", lower)
        if vol_pct_match:
            pct = int(vol_pct_match.group(1) or vol_pct_match.group(2) or vol_pct_match.group(3))
            success, msg = ComputerActions.set_volume(pct)
            resp = self.language.format_response("VOLUME_SET", f"{pct}", active_lang)
            return success, resp, False

        if any(w in lower for w in ["volume badhao", "volume up", "increase volume", "aawaz badhao"]):
            ComputerActions.volume_up()
            return True, "Volume increased, Sir.", False

        if any(w in lower for w in ["volume kam karo", "volume down", "decrease volume", "aawaz kam karo"]):
            ComputerActions.volume_down()
            return True, "Volume decreased, Sir.", False

        if any(w in lower for w in ["mute the laptop", "mute laptop", "mute karo", "unmute", "mute system", "mute"]):
            ComputerActions.toggle_mute()
            return True, "Mute toggled, Sir.", False

        if any(w in lower for w in ["pause music", "play music", "pause", "play", "pause media", "play media"]):
            ComputerActions.media_play_pause()
            return True, "Media playback toggled.", False

        if any(w in lower for w in ["next song", "next track", "skip track"]):
            ComputerActions.media_next()
            return True, "Skipped to next track.", False

        if any(w in lower for w in ["previous song", "previous track"]):
            ComputerActions.media_previous()
            return True, "Returning to previous track.", False

        # ----------------------------------------------------
        # 9. Window Management
        # ----------------------------------------------------
        if any(w in lower for w in ["minimize window", "minimize", "minimize the window"]):
            success, msg = WindowActions.minimize_window()
            return success, msg, False

        if any(w in lower for w in ["maximize window", "maximize", "maximize the window"]):
            success, msg = WindowActions.maximize_window()
            return success, msg, False

        if any(w in lower for w in ["restore window", "restore the window"]):
            success, msg = WindowActions.restore_window()
            return success, msg, False

        focus_match = re.search(r"(?:focus|switch to)\s+(?:window\s+)?([a-zA-Z0-9_\-\s]+)", lower)
        if focus_match:
            win_target = focus_match.group(1).strip()
            success, msg = WindowActions.focus_window(win_target)
            return success, msg, False

        # ----------------------------------------------------
        # 10. Screenshot & Clipboard
        # ----------------------------------------------------
        if any(w in lower for w in ["take a screenshot", "take screenshot", "screenshot le lo", "capture screen"]):
            success, msg = SystemActions.take_screenshot()
            resp = self.language.format_response("TAKE_SCREENSHOT", "", active_lang) if success else msg
            return success, resp, False

        if any(w in lower for w in ["read clipboard", "what is on my clipboard", "clipboard content"]):
            clip_text = pyperclip.paste()
            if not clip_text:
                return True, "Your clipboard is currently empty, Sir.", False
            if SecurityManager.sanitize_credential_input(clip_text):
                return True, "Security alert: Clipboard contains sensitive credential data.", False
            return True, f"Clipboard content: '{clip_text[:120]}'", False

        # ----------------------------------------------------
        # 11. File & Folder Search Engine
        # ----------------------------------------------------
        # "find assignment.pdf", "search my laptop for assignment.pdf", "find all pdf files", "find files containing networking"
        search_file_match = re.search(r"(?:search(?:\s+my\s+laptop)?(?:\s+for)?|find(?:\s+my)?)\s+(?:the\s+file\s+named\s+|file\s+named\s+|the\s+)?([a-zA-Z0-9_\-\.\s]+)", lower)
        if search_file_match and not any(w in lower for w in ["open", "close", "kholo", "band", "create", "delete", "make", "weather", "news", "youtube"]):
            search_item = search_file_match.group(1).strip()
            # Check extension filter
            ext_match = re.search(r"all\s+([a-zA-Z0-9]+)\s+files", search_item)
            ext = ext_match.group(1) if ext_match else None
            query_name = "" if ext else search_item

            files = FileActions.search_files(query_name, extension=ext, max_results=5)
            self.last_search_results = files
            if files:
                resp_lines = [f"I found {len(files)} matching file{'s' if len(files) > 1 else ''}:"]
                for i, f in enumerate(files, 1):
                    resp_lines.append(f"{i}. {f['name']} ({f['size_str']}) in {Path(f['path']).parent.name}")
                if len(files) == 1:
                    self.context.update("FOUND_FILE", files[0]["path"])
                    resp_lines.append(f"Say 'open it' if you'd like me to open {files[0]['name']}.")
                return True, "\n".join(resp_lines), False

            # Check folders
            folders = FileActions.search_folders(search_item, max_results=3)
            if folders:
                self.context.update("FOUND_FOLDER", folders[0]["path"])
                return True, f"I found the folder '{folders[0]['name']}' at {folders[0]['path']}. Say 'open it' to open.", False

            return False, f"Sorry {config.USER_NAME}, I could not find any files or folders matching '{search_item}'.", False

        # ----------------------------------------------------
        # 12. File & Folder Operations (Create, Delete, Open Specific)
        # ----------------------------------------------------
        # Folder Creation: "create a folder called College Project on my Desktop"
        folder_match = re.search(r"create(?:\s+a)?\s+folder\s+(?:called|named)?\s*([a-zA-Z0-9_\-\s]+?)(?:\s+on\s+my\s+(desktop|documents|downloads))?$", lower)
        if folder_match:
            fname = folder_match.group(1).strip()
            loc = folder_match.group(2).title() if folder_match.group(2) else "Desktop"
            success, msg = FileActions.create_folder(fname, parent_location=loc)
            return success, msg, False

        # Delete File/Folder: "delete oldproject.zip"
        delete_match = re.search(r"delete(?:\s+the\s+file|\s+the\s+folder)?\s+([a-zA-Z0-9_\-\.\s]+)", lower)
        if delete_match:
            del_target = delete_match.group(1).strip()
            # Search file first to resolve path
            found = FileActions.search_files(del_target, max_results=1) or FileActions.search_folders(del_target, max_results=1)
            if not found:
                return False, f"Could not find '{del_target}' to delete.", False

            target_path = found[0]["path"]
            action_desc = f"permanently delete '{Path(target_path).name}' from {Path(target_path).parent}"
            confirmed = SafetyGuard.request_confirmation(action_desc, tts_engine=self.tts)
            if confirmed:
                success, msg = FileActions.delete_path(target_path, confirmed=True)
                return success, msg, False
            return False, "Deletion cancelled by user.", False

        # Open Follow-up context ("open it")
        if lower in ["open it", "open that", "isse kholo", "open this"]:
            ctx = self.context.get_context()
            last_target = ctx.get("last_target") or ctx.get("last_app")
            if last_target:
                success, msg = FileActions.open_path(last_target)
                return success, msg, False
            return False, "No previous file or application context found to open.", False

        # Open Specific Files/Folders: "open the assignment PDF", "open my Downloads folder"
        open_folder_match = re.search(r"open(?:\s+my)?\s+(downloads|documents|desktop|pictures|videos|music)(?:\s+folder)?", lower)
        if open_folder_match:
            fol_name = open_folder_match.group(1).strip()
            target_fol = str(Path.home() / fol_name.capitalize())
            success, msg = FileActions.open_path(target_fol)
            return success, msg, False

        # ----------------------------------------------------
        # 13. Reminders & Notes & Long-Term Memory
        # ----------------------------------------------------
        if any(w in lower for w in ["yaad dilana", "remind me", "reminder lagao", "reminder set karo"]):
            success, details = self.reminders.parse_and_create(cleaned)
            resp = self.language.format_response("CREATE_REMINDER", details, active_lang)
            return success, resp, False

        note_match = re.search(r"(?:note karo|ek note banao|take a note|create a note)[:\s]+(.+)", lower)
        if note_match:
            content = note_match.group(1).strip()
            self.memory.add_note(title="Voice Note", content=content)
            resp = self.language.format_response("CREATE_NOTE", "", active_lang)
            return True, resp, False

        remember_match = re.search(r"(?:remember that|yaad rakhna ki|yaad rakho)\s+(.+)", lower)
        if remember_match:
            fact = remember_match.group(1).strip()
            success = self.memory.set_preference("user_fact", fact, category="facts")
            resp = f"I will remember that, {config.USER_NAME}." if success else "Security alert: Passwords or API keys cannot be stored."
            return True, resp, False

        if any(w in lower for w in ["forget that", "clear memory", "clear my memory"]):
            self.memory.clear_all_memory()
            return True, f"Memory has been cleared, {config.USER_NAME}.", False

        # ----------------------------------------------------
        # 14. Web Searches (Google, YouTube, News, Weather)
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
                success, _ = WebActions.search_youtube(search_query)
                self.context.update("SEARCH_YOUTUBE", search_query)
                resp = self.language.format_response("SEARCH_YOUTUBE", search_query, active_lang)
                return success, resp, False

        google_match = re.search(r"(?:search\s+(?:for\s+|google\s+for\s+|on\s+google\s+)?|google\s+par\s+search\s+karo\s+|google\s+)(.+)", lower)
        if google_match and ("search" in lower or "google" in lower):
            search_query = google_match.group(1).replace("on google", "").replace("google", "").replace("par", "").replace("search", "").replace("karo", "").strip()
            if search_query:
                success, _ = WebActions.search_google(search_query)
                self.context.update("SEARCH_WEB", search_query)
                resp = self.language.format_response("SEARCH_WEB", search_query, active_lang)
                return success, resp, False

        # ----------------------------------------------------
        # 15. Close Application
        # ----------------------------------------------------
        close_target = None
        if any(w in lower for w in ["close", "band karo", "band kar do", "kill"]):
            close_clean = lower
            for phrase in ["band karo", "band kar do", "band", "close", "kill", "please", "app", "application"]:
                close_clean = close_clean.replace(phrase, "")
            close_target = close_clean.strip()

        if close_target:
            success, msg = ComputerActions.close_app(close_target)
            resp = self.language.format_response("CLOSE_APP", close_target.title(), active_lang) if success else msg
            return success, resp, False

        # ----------------------------------------------------
        # 16. Open Websites or Applications
        # ----------------------------------------------------
        open_target = None
        if any(w in lower for w in ["open", "kholo", "khol do", "open karo", "chalao", "launch", "start"]):
            target_clean = lower
            for phrase in [
                "i want to open", "can you open", "please open", "open for me",
                "open karo", "khol do", "khol na", "kholo", "chalao", "launch",
                "start", "open", "please"
            ]:
                target_clean = target_clean.replace(phrase, "")
            
            # Special aliases
            if "whatsapp" in target_clean or "whats app" in target_clean:
                open_target = "whatsapp"
            else:
                for filler in ["my", "the", "mera", "meri", "apna", "apni", "website", "site", "browser", "app", "application", "for me", "i want"]:
                    target_clean = re.sub(rf'\b{filler}\b', '', target_clean, flags=re.IGNORECASE).strip()
                open_target = target_clean.strip()

        if open_target:
            from jarvis.actions.web_actions import POPULAR_SITES
            matched_site = None
            for site_key in POPULAR_SITES.keys():
                if site_key == open_target.lower():
                    matched_site = site_key
                    break

            if matched_site or "." in open_target:
                target_url = matched_site if matched_site else open_target
                success, res_target = WebActions.open_website(target_url)
                self.context.update("OPEN_WEBSITE", target_url)
                resp = self.language.format_response("OPEN_APP", target_url.title(), active_lang)
                return success, resp, False

            # Check if desktop application
            success, app_res = AppActions.open_app(open_target, tts_engine=self.tts)
            if success:
                self.context.update("OPEN_APP", open_target)
                resp = self.language.format_response("OPEN_APP", open_target.title(), active_lang)
                return True, resp, False
            else:
                # Check if it's a file on the computer
                found_files = FileActions.search_files(open_target, max_results=1)
                if found_files:
                    success, msg = FileActions.open_path(found_files[0]["path"])
                    self.context.update("OPEN_FILE", found_files[0]["path"])
                    return success, f"Opened '{found_files[0]['name']}', {config.USER_NAME}.", False

                # Fallback to web search/domain
                success, res_target = WebActions.open_website(open_target)
                if success:
                    self.context.update("OPEN_WEBSITE", open_target)
                    resp = self.language.format_response("OPEN_APP", open_target.title(), active_lang)
                    return True, resp, False

                resp = self.language.format_response("APP_NOT_FOUND", open_target.title(), active_lang)
                return False, resp, False

        # ----------------------------------------------------
        # 17. Fallback to AI Brain (Knowledge & Dialogue)
        # ----------------------------------------------------
        recent_history = self.memory.get_recent_conversations(limit=4)
        ai_response = self.brain.ask(cleaned, conversation_history=recent_history)
        self.memory.log_action(cleaned, "AI_CONVERSATION", "SUCCESS", ai_response)
        return True, ai_response, False
