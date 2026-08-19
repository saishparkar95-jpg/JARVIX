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


# Disallowed operations that could damage the system or leak private data
BLOCKED_PATTERNS = [
    r"\brmdir\s+/s\b",
    r"\bdel\s+/[fqsa]\b",
    r"\bformat\s+[a-z]:\b",
    r"\bshutdown\b",
    r"\brestart\b",
    r"\breg\s+delete\b",
    r"\bpowershell\s+-enc\b",
    r"\bnet\s+user\b",
    r"\bnetsh\b",
    r"\bdrop\s+database\b",
    r"\bdelete\s+from\b"
]

# Sensitive system directories where modifying files/folders is strictly forbidden
RESTRICTED_SYSTEM_DIRS = [
    os.path.normpath(r"c:\windows").lower(),
    os.path.normpath(r"c:\program files").lower(),
    os.path.normpath(r"c:\program files (x86)").lower(),
    os.path.normpath(r"c:\system32").lower()
]


class SafetyGuard:
    """Enforces safety rules and requests user confirmation when required."""

    @staticmethod
    def is_command_safe(command: str) -> Tuple[bool, str]:
        """Checks if a command contains blocked patterns or dangerous system modifications."""
        cmd_lower = command.lower()
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, cmd_lower):
                return False, f"Action blocked: Command matches restricted pattern '{pattern}'."

        return True, "Safe"

    @staticmethod
    def is_path_safe(target_path: Path) -> Tuple[bool, str]:
        """Validates that a path is not in protected Windows system directories."""
        try:
            norm_target = os.path.normpath(os.path.abspath(str(target_path))).lower()
            for restricted in RESTRICTED_SYSTEM_DIRS:
                if norm_target == restricted or norm_target.startswith(restricted + os.sep) or norm_target.startswith(restricted):
                    return False, f"Action blocked: Modifying system directory '{restricted}' is not permitted."
            return True, "Safe"
        except Exception as e:
            return False, f"Invalid path resolution: {e}"

    @staticmethod
    def request_confirmation(action_description: str, tts_engine=None) -> bool:
        """
        Prompts the user for explicit confirmation before executing sensitive actions.
        Can ask via voice/terminal.
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
