"""
jarvis/actions/app_actions.py
Application launcher with strict application allowlist and confirmation for unknown apps.
"""

import os
import subprocess
import shutil
from typing import Tuple, Optional
import config
from jarvis.actions.safety import SafetyGuard


# Extended registry of safe and common Windows applications
APPLICATION_ALLOWLIST = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "chrome": [
        "chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ],
    "google chrome": [
        "chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ],
    "edge": [
        "msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ],
    "microsoft edge": [
        "msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ],
    "firefox": ["firefox.exe", r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
        "spotify.exe"
    ],
    "vscode": [
        "code.cmd",
        "code.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe"
    ],
    "vs code": [
        "code.cmd",
        "code.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe"
    ],
    "code": [
        "code.cmd",
        "code.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe"
    ],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "downloads": [os.path.expandvars(r"%USERPROFILE%\Downloads")],
    "documents": [os.path.expandvars(r"%USERPROFILE%\Documents")],
    "desktop": [os.path.expandvars(r"%USERPROFILE%\Desktop")],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "paint": ["mspaint.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "vlc": ["vlc.exe", r"C:\Program Files\VideoLAN\VLC\vlc.exe"],
    "discord": [os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe")],
    "telegram": [os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe")],
    "whatsapp": ["whatsapp.exe", os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"), os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\WhatsApp.exe")],
    "whats app": ["whatsapp.exe", os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"), os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\WhatsApp.exe")],
    "task manager": ["taskmgr.exe"],
    "settings": ["ms-settings:"],
    "control panel": ["control.exe"]
}


class AppActions:
    """Safely discovers and launches Windows applications and associated target files/folders."""

    @staticmethod
    def open_app(app_name: str, target_arg: str = None, tts_engine=None) -> Tuple[bool, str]:
        """
        Attempts to launch the requested application, optionally passing a file/folder target.
        (e.g. open VS Code with project folder path).
        """
        app_key = app_name.lower().strip()

        # 1. Check direct Allowlist candidates
        is_known = app_key in APPLICATION_ALLOWLIST
        candidates = APPLICATION_ALLOWLIST.get(app_key, [])

        # 2. Check if Start Menu shortcut exists
        if not candidates:
            shortcut = AppActions._find_start_menu_app(app_key)
            if shortcut:
                candidates = [shortcut]
                is_known = True

        if not is_known and not candidates:
            # Fallback to system command check (e.g. app_name.exe)
            if shutil.which(f"{app_key}.exe") or shutil.which(app_key):
                candidates = [f"{app_key}.exe"]
                is_known = True

        if not is_known:
            action_desc = f"open unregistered application '{app_name}'"
            if not SafetyGuard.request_confirmation(action_desc, tts_engine=tts_engine):
                return False, f"Opening '{app_name}' was cancelled for security reasons."
            candidates = [f"{app_key}.exe", app_key]

        for candidate in candidates:
            try:
                # URI protocol check (e.g. ms-settings:)
                if candidate.endswith(":"):
                    os.startfile(candidate)
                    return True, app_name.title()

                # Full path or shortcut execution
                if os.path.exists(candidate) or shutil.which(candidate):
                    if target_arg:
                        subprocess.Popen([candidate, str(target_arg)], shell=False)
                    else:
                        os.startfile(candidate)
                    return True, app_name.title()

                # Command execution
                if target_arg:
                    subprocess.Popen([candidate, str(target_arg)], shell=True)
                else:
                    subprocess.Popen([candidate], shell=True)
                return True, app_name.title()
            except Exception:
                continue

        return False, f"Could not launch '{app_name}'. Application may not be installed."

    @staticmethod
    def _find_start_menu_app(app_name: str) -> Optional[str]:
        """Searches Windows Start Menu shortcuts (.lnk) for installed desktop programs."""
        start_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
        ]
        clean_name = app_name.lower()
        for sdir in start_dirs:
            if os.path.exists(sdir):
                for root, _, files in os.walk(sdir):
                    for f in files:
                        if f.lower().endswith(".lnk") and clean_name in f.lower():
                            return os.path.join(root, f)
        return None
