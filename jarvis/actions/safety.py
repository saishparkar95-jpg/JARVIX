"""
jarvis/actions/safety.py
Safety engine ensuring secure and validated execution of actions.
Enforces confirmation for sensitive tasks and blocks hazardous operations.
"""

import os
import re
from pathlib import Path
from typing import Tuple
import config


from jarvis.core.security_manager import SecurityManager, PermissionLevel, BLOCKED_PATTERNS, RESTRICTED_SYSTEM_DIRS


class SafetyGuard:
    """Enforces safety rules and requests user confirmation when required."""

    @staticmethod
    def is_command_safe(command: str) -> Tuple[bool, str]:
        """Checks if a command contains blocked patterns or dangerous system modifications."""
        perm, reason = SecurityManager.validate_action("RUN_COMMAND", command)
        if perm == PermissionLevel.LEVEL_3_BLOCKED:
            return False, f"Action blocked: {reason}"
        return True, "Safe"

    @staticmethod
    def is_path_safe(target_path: Path) -> Tuple[bool, str]:
        """Validates that a path is not in protected Windows system directories."""
        return SecurityManager.is_path_safe(target_path)

    @staticmethod
    def request_confirmation(action_description: str, tts_engine=None) -> bool:
        """
        Prompts the user for explicit confirmation before executing sensitive actions.
        Can ask via voice/terminal/dialog.
        """
        if not config.REQUIRE_CONFIRMATION:
            return True

        prompt_msg = f"Security check: Are you sure you want to proceed with: '{action_description}'? (yes/no)"
        if tts_engine:
            tts_engine.speak(f"Please confirm: Do you want me to {action_description}?")

        print(f"\n\033[93m[SECURITY CONFIRMATION]\033[0m: {prompt_msg}")
        try:
            response = input("\033[93m[Confirm (yes/no)]\033[0m: ").strip().lower()
            return response in ["yes", "y", "confirm", "proceed", "sure"]
        except (KeyboardInterrupt, EOFError):
            return False
