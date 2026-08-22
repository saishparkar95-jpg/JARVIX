"""
jarvis/actions/window_actions.py
Windows Window Management: List, Focus, Minimize, Maximize, Restore, and Switch.
Uses Win32 native APIs via pywin32 / ctypes for direct control without shell overhead.
"""

import ctypes
from typing import List, Dict, Optional, Tuple, Any

try:
    import win32gui
    import win32con
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class WindowActions:
    """Provides safe window management controls for Windows applications."""

    @staticmethod
    def get_open_windows() -> List[Dict[str, Any]]:
        """Returns a list of all visible, named desktop windows."""
        if not HAS_WIN32:
            return []

        windows = []
        def _enum_handler(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd).strip():
                # Filter out tooltips and system overlays
                title = win32gui.GetWindowText(hwnd).strip()
                if len(title) > 1 and title not in ["Program Manager", "Settings"]:
                    windows.append({
                        "hwnd": hwnd,
                        "title": title
                    })
        try:
            win32gui.EnumWindows(_enum_handler, None)
        except Exception:
            pass
        return windows

    @staticmethod
    def find_window_by_name(name_query: str) -> Optional[int]:
        """Finds the first window HWND matching the application/window name query."""
        if not name_query or not HAS_WIN32:
            return None

        clean_query = name_query.lower().strip()
        open_windows = WindowActions.get_open_windows()

        # 1. Exact or substring match
        for win in open_windows:
            if clean_query in win["title"].lower():
                return win["hwnd"]
        return None

    @staticmethod
    def focus_window(app_or_window_name: str) -> Tuple[bool, str]:
        """Brings the requested window to the foreground."""
        hwnd = WindowActions.find_window_by_name(app_or_window_name)
        if not hwnd or not HAS_WIN32:
            return False, f"Window for '{app_or_window_name}' not found."

        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            title = win32gui.GetWindowText(hwnd)
            return True, f"Focused '{title}'."
        except Exception as e:
            return False, f"Failed to focus window: {e}"

    @staticmethod
    def minimize_window(app_or_window_name: Optional[str] = None) -> Tuple[bool, str]:
        """Minimizes the requested window, or the current foreground window if None."""
        if not HAS_WIN32:
            return False, "Win32 API not available."

        try:
            if app_or_window_name:
                hwnd = WindowActions.find_window_by_name(app_or_window_name)
            else:
                hwnd = win32gui.GetForegroundWindow()

            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return True, "Window minimized."
            return False, "No active window found to minimize."
        except Exception as e:
            return False, f"Failed to minimize window: {e}"

    @staticmethod
    def maximize_window(app_or_window_name: Optional[str] = None) -> Tuple[bool, str]:
        """Maximizes the requested window, or the current foreground window."""
        if not HAS_WIN32:
            return False, "Win32 API not available."

        try:
            if app_or_window_name:
                hwnd = WindowActions.find_window_by_name(app_or_window_name)
            else:
                hwnd = win32gui.GetForegroundWindow()

            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                return True, "Window maximized."
            return False, "No active window found to maximize."
        except Exception as e:
            return False, f"Failed to maximize window: {e}"

    @staticmethod
    def restore_window(app_or_window_name: Optional[str] = None) -> Tuple[bool, str]:
        """Restores a minimized or maximized window."""
        if not HAS_WIN32:
            return False, "Win32 API not available."

        try:
            if app_or_window_name:
                hwnd = WindowActions.find_window_by_name(app_or_window_name)
            else:
                hwnd = win32gui.GetForegroundWindow()

            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                return True, "Window restored."
            return False, "No window found to restore."
        except Exception as e:
            return False, f"Failed to restore window: {e}"
