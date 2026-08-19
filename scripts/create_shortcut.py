"""
create_shortcut.py
Creates a 1-click Windows Desktop shortcut for JARVIS.
"""

import os
from pathlib import Path
import win32com.client

def create_desktop_shortcut():
    onedrive_desktop = Path(os.environ["USERPROFILE"]) / "OneDrive" / "Desktop"
    standard_desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    desktop = onedrive_desktop if onedrive_desktop.exists() else standard_desktop

    project_dir = Path(__file__).resolve().parent.parent
    exe_target = project_dir / "dist" / "JARVIS" / "JARVIS.exe"
    shortcut_path = desktop / "JARVIS AI.lnk"

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = str(exe_target)
    shortcut.WorkingDirectory = str(exe_target.parent)
    shortcut.Description = "JARVIS AI Windows Desktop Assistant"
    shortcut.Save()
    print(f"Updated shortcut on Desktop at: {shortcut_path}")

if __name__ == "__main__":
    create_desktop_shortcut()
