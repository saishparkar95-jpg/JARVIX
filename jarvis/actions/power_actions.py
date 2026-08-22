"""
jarvis/actions/power_actions.py
Safe Windows Power Operations: Shutdown, Restart, Sleep, Lock, and Cancel.
Always enforces security confirmation and safety windows before executing.
"""

import os
import ctypes
import subprocess
from typing import Tuple
from jarvis.core.security_manager import SecurityManager, PermissionLevel


class PowerActions:
    """Controls laptop power states with mandatory confirmation safeguards."""

    @staticmethod
    def lock_workstation() -> Tuple[bool, str]:
        """Immediately locks the Windows computer session safely (Level 1 Safe)."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "Workstation locked successfully."
        except Exception as e:
            return False, f"Failed to lock workstation: {e}"

    @staticmethod
    def sleep_laptop(confirmed: bool = False) -> Tuple[bool, str]:
        """Puts the Windows computer to sleep (Level 2 Confirmation)."""
        if not confirmed:
            return False, "Sleep requires explicit user confirmation."

        try:
            # Call Windows Powrprof SetSuspendState(0, 1, 0)
            res = ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
            return True, "Putting the computer to sleep."
        except Exception as e:
            return False, f"Failed to put laptop to sleep: {e}"

    @staticmethod
    def restart_laptop(confirmed: bool = False, delay_seconds: int = 20) -> Tuple[bool, str]:
        """Initiates Windows restart with a cancellation window (Level 2 Confirmation)."""
        if not confirmed:
            return False, "Restart requires explicit user confirmation."

        try:
            subprocess.run(["shutdown", "/r", "/t", str(delay_seconds), "/c", "JARVIS restart scheduled. Say 'Cancel shutdown' to abort."], check=True)
            return True, f"Restarting Windows in {delay_seconds} seconds. You can say 'Cancel shutdown' to abort."
        except Exception as e:
            return False, f"Failed to schedule restart: {e}"

    @staticmethod
    def shutdown_laptop(confirmed: bool = False, delay_seconds: int = 20) -> Tuple[bool, str]:
        """Initiates Windows shutdown with a cancellation window (Level 2 Confirmation)."""
        if not confirmed:
            return False, "Shutdown requires explicit user confirmation."

        try:
            subprocess.run(["shutdown", "/s", "/t", str(delay_seconds), "/c", "JARVIS shutdown scheduled. Say 'Cancel shutdown' to abort."], check=True)
            return True, f"Shutting down Windows in {delay_seconds} seconds. You can say 'Cancel shutdown' to abort."
        except Exception as e:
            return False, f"Failed to schedule shutdown: {e}"

    @staticmethod
    def cancel_shutdown() -> Tuple[bool, str]:
        """Aborts any scheduled shutdown or restart."""
        try:
            subprocess.run(["shutdown", "/a"], check=True)
            return True, "Scheduled shutdown or restart has been cancelled."
        except Exception as e:
            return False, "No active shutdown was scheduled or failed to cancel."
