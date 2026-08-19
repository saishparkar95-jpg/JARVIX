"""
build_exe.py
Build script to package JARVIS AI Assistant into a standalone Windows executable using PyInstaller.
"""

import os
import sys
import subprocess
from pathlib import Path


def build():
    print("=" * 60)
    print("       Building JARVIS AI Windows Executable (JARVIS.exe)       ")
    print("=" * 60)

    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    root_dir = Path(__file__).resolve().parent.parent
    main_script = root_dir / "main.py"
    icon_path = root_dir / "assets" / "icon.ico"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=JARVIS",
        "--noconfirm",
        "--onedir",             # One-folder distribution for highest stability
        "--windowed",           # GUI mode without console popup
        f"--add-data={root_dir / '.env.example'};.",
        f"--add-data={root_dir / 'config.py'};.",
        "--clean",
        str(main_script)
    ]

    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    print("\n" + "=" * 60)
    print("Build Complete! Your executable is located at: dist/JARVIS/JARVIS.exe")
    print("=" * 60)


if __name__ == "__main__":
    build()
