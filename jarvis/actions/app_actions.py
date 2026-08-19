"""
jarvis/actions/app_actions.py
Application launcher with strict application allowlist and confirmation for unknown apps.
"""

import os
import subprocess
import shutil
from typing import Tuple
import config
from jarvis.actions.safety import SafetyGuard


# Official Allowlist of verified safe applications
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
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ],
    "microsoft edge": [
        "msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ],
    "firefox": ["firefox.exe", r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
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
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "cmd": ["cmd.exe"],
    "paint": ["mspaint.exe"]
}


class AppActions:
    """Safely launches registered and installed Windows applications."""

    @staticmethod
    def open_app(app_name: str, tts_engine=None) -> Tuple[bool, str]:
        """
        Attempts to launch the requested application.
        If application is not in allowlist, requires user confirmation before proceeding.
        """
        app_key = app_name.lower().strip()

        # Check if in Allowlist
        is_known = app_key in APPLICATION_ALLOWLIST
        candidates = APPLICATION_ALLOWLIST.get(app_key, [f"{app_key}.exe", app_key])

        if not is_known:
            # Unregistered application: request user confirmation
            action_desc = f"open unregistered application '{app_name}'"
            if not SafetyGuard.request_confirmation(action_desc, tts_engine=tts_engine):
                return False, f"Opening '{app_name}' was cancelled for security reasons."

        for candidate in candidates:
            # Full path check
            if os.path.isabs(candidate) and os.path.exists(candidate):
                try:
                    os.startfile(candidate)
                    return True, f"{app_name}"
                except Exception as e:
                    return False, f"Could not launch {app_name}: {e}"

            # PATH check
            resolved = shutil.which(candidate)
            if resolved:
                try:
                    subprocess.Popen([resolved], shell=False)
                    return True, f"{app_name}"
                except Exception as e:
                    return False, f"Error launching {app_name}: {e}"

        # Fallback to os.startfile for Windows shell associations
        try:
            os.startfile(app_key)
            return True, f"{app_name}"
        except Exception:
            return False, f"{app_name}"
