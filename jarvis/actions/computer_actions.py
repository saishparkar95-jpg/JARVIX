"""
jarvis/actions/computer_actions.py
Laptop hardware and OS automation: Volume, Media playback, Screen lock, File operations.
"""

import os
import ctypes
import subprocess
from pathlib import Path
from typing import Tuple, List
import pyautogui
import config
from jarvis.actions.safety import SafetyGuard


class ComputerActions:
    """Safe controls for laptop multimedia, screen lock, and file utilities."""

    @staticmethod
    def set_volume(level_percent: int) -> Tuple[bool, str]:
        """Sets Windows system volume (0-100%)."""
        try:
            # Clamp percentage
            clamped = max(0, min(100, level_percent))
            # Approximate volume adjustment using native Windows volume keys
            # First mute/zero, then step up
            for _ in range(50):
                pyautogui.press('volumedown')
            steps_up = int(clamped / 2)
            for _ in range(steps_up):
                pyautogui.press('volumeup')
            return True, f"{clamped}%"
        except Exception as e:
            return False, f"Could not adjust volume: {e}"

    @staticmethod
    def volume_up() -> Tuple[bool, str]:
        """Increases volume by 10%."""
        for _ in range(5):
            pyautogui.press('volumeup')
        return True, "Volume increased"

    @staticmethod
    def volume_down() -> Tuple[bool, str]:
        """Decreases volume by 10%."""
        for _ in range(5):
            pyautogui.press('volumedown')
        return True, "Volume decreased"

    @staticmethod
    def toggle_mute() -> Tuple[bool, str]:
        """Mutes or unmutes system sound."""
        pyautogui.press('volumemute')
        return True, "Mute toggled"

    @staticmethod
    def media_play_pause() -> Tuple[bool, str]:
        """Plays or pauses media playback."""
        pyautogui.press('playpause')
        return True, "Media playback toggled"

    @staticmethod
    def media_next() -> Tuple[bool, str]:
        """Skips to next media track."""
        pyautogui.press('nexttrack')
        return True, "Next track"

    @staticmethod
    def media_previous() -> Tuple[bool, str]:
        """Skips to previous media track."""
        pyautogui.press('prevtrack')
        return True, "Previous track"

    @staticmethod
    def lock_workstation() -> Tuple[bool, str]:
        """Locks the Windows computer workstation safely."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "Workstation locked successfully."
        except Exception as e:
            return False, f"Failed to lock workstation: {e}"

    @staticmethod
    def close_app(app_name: str) -> Tuple[bool, str]:
        """
        Safely closes an application from the allowlist.
        Does not terminate essential Windows system processes.
        """
        safe_process_names = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "CalculatorApp.exe",
            "calc": "CalculatorApp.exe",
            "spotify": "Spotify.exe",
            "vscode": "Code.exe",
            "vs code": "Code.exe",
            "code": "Code.exe",
            "edge": "msedge.exe",
            "paint": "mspaint.exe"
        }

        clean_name = app_name.lower().strip()
        exe_name = safe_process_names.get(clean_name)

        if not exe_name:
            return False, f"Cannot terminate '{app_name}'. Process is not in safe termination registry."

        try:
            subprocess.run(["taskkill", "/F", "/IM", exe_name], capture_output=True, text=True, check=False)
            return True, f"{app_name} has been closed."
        except Exception as e:
            return False, f"Could not close {app_name}: {e}"

    @staticmethod
    def search_files(keyword: str, search_dir: Path = None) -> Tuple[bool, List[str]]:
        """
        Safely searches for files matching keyword in allowed user directories.
        """
        if not keyword or len(keyword.strip()) < 2:
            return False, ["Keyword is too short."]

        target_dir = search_dir or Path.home() / "Desktop"
        is_safe, msg = SafetyGuard.is_path_safe(target_dir)
        if not is_safe:
            return False, [msg]

        matches = []
        try:
            for item in target_dir.rglob(f"*{keyword}*"):
                if item.is_file():
                    matches.append(str(item))
                    if len(matches) >= 5:
                        break
            return True, matches if matches else ["No matching files found."]
        except Exception as e:
            return False, [f"Error searching files: {e}"]

    @staticmethod
    def create_file(file_name: str, content: str = "", target_dir: Path = None) -> Tuple[bool, str]:
        """
        Safely creates a new text file in allowed directory.
        """
        clean_name = "".join(c for c in file_name if c.isalnum() or c in (" ", "_", "-", ".")).strip()
        if not clean_name:
            return False, "Invalid file name."

        target_dir = target_dir or Path.home() / "Desktop"
        file_path = target_dir / clean_name

        is_safe, msg = SafetyGuard.is_path_safe(file_path)
        if not is_safe:
            return False, msg

        try:
            file_path.write_text(content, encoding="utf-8")
            return True, f"File '{clean_name}' created successfully at {target_dir}."
        except Exception as e:
            return False, f"Error creating file: {e}"
