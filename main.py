"""
main.py
Universal entry point for JARVIS AI Assistant.
Launches the Futuristic Desktop GUI by default, or Terminal CLI mode when requested.
"""

import sys
import argparse
import config


def run_gui(start_minimized: bool = False):
    """Launches the PySide6 Desktop GUI."""
    try:
        from PySide6.QtWidgets import QApplication
        from jarvis.ui.main_window import MainWindow
    except ImportError as e:
        print(f"\033[91m[Error loading GUI: {e}. Falling back to CLI mode.]\033[0m")
        run_cli("voice")
        return

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow(start_minimized=start_minimized)
    if not start_minimized:
        window.show()

    sys.exit(app.exec())


def run_cli(mode: str):
    """Launches the Terminal CLI version."""
    from jarvis.assistant import JarvisAssistant
    config.INPUT_MODE = mode
    assistant = JarvisAssistant()
    assistant.run()


def main():
    parser = argparse.ArgumentParser(description="JARVIS AI - Windows Desktop Assistant")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in terminal CLI mode instead of GUI."
    )
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default=None,
        help="Input mode: 'voice' for microphone, 'text' for console typing."
    )
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start minimized in Windows System Tray (for background boot)."
    )
    args = parser.parse_args()

    # If --cli or --mode text is explicitly requested, run terminal mode
    if args.cli or args.mode:
        selected_mode = args.mode if args.mode else "voice"
        run_cli(selected_mode)
    else:
        # Default: Launch the Futuristic Desktop Application
        run_gui(start_minimized=args.minimized)


if __name__ == "__main__":
    main()
