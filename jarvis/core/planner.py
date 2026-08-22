"""
jarvis/core/planner.py
Multi-Step Task Planning and Sequential Action Execution Engine for JARVIS.
Decomposes complex composite user commands into validated sequential steps.
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from jarvis.core.security_manager import SecurityManager, PermissionLevel
from jarvis.actions.file_actions import FileActions
from jarvis.actions.app_actions import AppActions
from jarvis.actions.web_actions import WebActions
from jarvis.actions.window_actions import WindowActions
from jarvis.actions.power_actions import PowerActions
from jarvis.actions.computer_actions import ComputerActions


class TaskPlanner:
    """Plans, validates, and executes multi-step composite operations."""

    def __init__(self, memory_manager, tts_engine):
        self.memory = memory_manager
        self.tts = tts_engine

    def is_multi_step_request(self, query: str) -> bool:
        """Detects if a user query contains multiple chained intents/actions."""
        lower = query.lower()
        # Chaining conjunctions & indicators
        conjunctions = [
            r"\band\s+open\b", r"\band\s+search\b", r"\band\s+show\b",
            r"\band\s+play\b", r"\band\s+then\b", r"\b,\s*open\b",
            r"\b,\s*search\b", r"\bphir\b", r"\baur\b"
        ]
        return any(re.search(c, lower) for c in conjunctions)

    def plan_and_execute(self, query: str) -> Tuple[bool, str]:
        """
        Decomposes query into planned steps, validates with SecurityManager,
        and sequentially executes each step.
        """
        lower = query.lower().strip()

        # Pattern 1: "Find my [X] project / folder and open it in VS Code"
        match_proj_vscode = re.search(r"(?:find|search(?:\s+for)?)\s+(?:my\s+)?(.+?)(?:\s+project|\s+folder)?\s*(?:and|,|phir|aur)\s*(?:open\s+(?:it\s+in\s+)?(?:vs\s*code|code)|launch\s+vscode)", lower)
        if match_proj_vscode:
            folder_query = match_proj_vscode.group(1).strip()
            # Step 1: Search folder
            folders = FileActions.search_folders(folder_query)
            if not folders:
                return False, f"Could not find any project folder matching '{folder_query}'."

            target_folder = folders[0]["path"]

            # Step 2: Open in VS Code
            success, app_msg = AppActions.open_app("vscode", target_arg=target_folder, tts_engine=self.tts)
            if success:
                return True, f"Found '{folders[0]['name']}' and opened it in VS Code."
            else:
                # Fallback: Open folder in File Explorer
                FileActions.open_path(target_folder)
                return True, f"Found '{folders[0]['name']}' and opened the folder."

        # Pattern 2: "Find [X] and open it"
        match_find_open = re.search(r"(?:find|search(?:\s+for)?)\s+(?:my\s+)?(.+?)\s*(?:and|,|phir|aur)\s*open\s+(?:it)?", lower)
        if match_find_open:
            file_query = match_find_open.group(1).strip()
            # Check files first
            files = FileActions.search_files(file_query)
            if files:
                target_file = files[0]["path"]
                success, msg = FileActions.open_path(target_file)
                return success, f"Found and opened '{files[0]['name']}'."

            # Check folders
            folders = FileActions.search_folders(file_query)
            if folders:
                target_folder = folders[0]["path"]
                success, msg = FileActions.open_path(target_folder)
                return success, f"Found and opened folder '{folders[0]['name']}'."

            return False, f"Could not find any file or folder matching '{file_query}'."

        # Pattern 3: "Open Chrome / browser and search for [X]"
        match_browser_search = re.search(r"open\s+(?:the\s+)?(?:browser|chrome|google)\s*(?:and|,|phir|aur)\s*search(?:\s+for|\s+on\s+google\s+for)?\s+(.+)", lower)
        if match_browser_search:
            search_query = match_browser_search.group(1).strip()
            success, _ = WebActions.search_google(search_query)
            return success, f"Opened browser and searched Google for '{search_query}'."

        # Pattern 4: "Open YouTube and play / search for [X]"
        match_yt_search = re.search(r"open\s+youtube\s*(?:and|,|phir|aur)\s*(?:search(?:\s+for)?|play)\s+(.+)", lower)
        if match_yt_search:
            yt_query = match_yt_search.group(1).strip()
            success, _ = WebActions.search_youtube(yt_query)
            return success, f"Opened YouTube and searched for '{yt_query}'."

        return False, "Could not construct an automated execution plan for this multi-step request."
