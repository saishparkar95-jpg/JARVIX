"""
setup_startup.py
Enables automatic startup with Windows so JARVIS is always running in the background.
"""

import os
import sys
from pathlib import Path
import win32com.client


def enable_windows_startup():
    startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    project_dir = Path(__file__).resolve().parent.parent
    vbs_target = project_dir / "Run_JARVIS.vbs"
    shortcut_path = startup_dir / "JARVIS AI.lnk"

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = str(vbs_target)
    shortcut.WorkingDirectory = str(project_dir)
    shortcut.Description = "JARVIS AI Always-On Background Assistant"
    shortcut.Save()

    print(f"\n========================================================")
    print(f"[SUCCESS] JARVIS has been added to Windows Startup!")
    print(f"Location: {shortcut_path}")
    print(f"JARVIS will now automatically run silently in the background")
    print(f"whenever you turn on your laptop!")
    print(f"========================================================\n")


def disable_windows_startup():
    startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    shortcut_path = startup_dir / "JARVIS AI.lnk"
    if shortcut_path.exists():
        shortcut_path.unlink()
        print("JARVIS removed from Windows Startup.")
    else:
        print("JARVIS was not in Windows Startup.")


if __name__ == "__main__":
    enable_windows_startup()
