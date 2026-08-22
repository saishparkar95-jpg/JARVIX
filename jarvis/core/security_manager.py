"""
jarvis/core/security_manager.py
Security Architecture for JARVIS: 3-Tier Permission Level Engine, Path Traversal Protection,
and Confirmation Handler.

Security Pipeline:
AI / User Request -> Structured Action -> Action Validator -> Security Manager -> SAFE / CONFIRM / BLOCK -> Execution
"""

import os
import re
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import config


class PermissionLevel:
    LEVEL_1_SAFE = 1           # Can execute immediately without confirmation
    LEVEL_2_CONFIRM = 2        # Requires explicit user confirmation (Voice / GUI Dialog)
    LEVEL_3_BLOCKED = 3        # Strict forbidden action, never executed automatically


# Blocked hazardous system commands and shell patterns
BLOCKED_PATTERNS = [
    r"\brmdir\s+/[sS]\b",
    r"\bdel\s+/[fFqQsSaA]\b",
    r"\bformat\s+[a-zA-Z]:",
    r"\bshutdown\b",
    r"\brestart\b",
    r"\breg\s+(delete|add)\b",
    r"\bpowershell\s+.*-enc\b",
    r"\bnet\s+user\b",
    r"\bnet\s+localgroup\b",
    r"\bnetsh\b",
    r"\bdiskpart\b",
    r"\bvssadmin\s+delete\b",
    r"\bbcdedit\b",
    r"\bSet-MpPreference\b",
    r"\bDisableRealtimeMonitoring\b",
    r"\bdrop\s+database\b",
    r"\bdelete\s+from\b"
]

# Sensitive system directories where modifying or deleting files/folders is strictly forbidden
RESTRICTED_SYSTEM_DIRS = [
    os.path.normpath(r"c:\windows").lower(),
    os.path.normpath(r"c:\program files").lower(),
    os.path.normpath(r"c:\program files (x86)").lower(),
    os.path.normpath(r"c:\system32").lower(),
    os.path.normpath(os.environ.get("SystemRoot", r"C:\Windows")).lower(),
    os.path.normpath(os.environ.get("ProgramFiles", r"C:\Program Files")).lower(),
    os.path.normpath(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).lower() if "ProgramFiles(x86)" in os.environ else None
]
RESTRICTED_SYSTEM_DIRS = [d for d in RESTRICTED_SYSTEM_DIRS if d]

# Allowed safe base directories for unrestricted file operations
ALLOWED_USER_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Videos",
    Path.home() / "Music",
    config.BASE_DIR
]


class SecurityManager:
    """Enforces 3-tier security permissions, validates paths, and protects user credentials."""

    @staticmethod
    def validate_action(action_type: str, target: Any = None, details: Dict[str, Any] = None) -> Tuple[int, str]:
        """
        Classifies an action into LEVEL_1_SAFE, LEVEL_2_CONFIRM, or LEVEL_3_BLOCKED.
        Returns: (PermissionLevel, Reason / Description)
        """
        action_upper = action_type.upper().strip()
        details = details or {}

        # =========================================================================
        # LEVEL 3 — STRICTLY BLOCKED ACTIONS
        # =========================================================================
        blocked_actions = [
            "DISABLE_ANTIVIRUS", "DISABLE_DEFENDER", "DISABLE_FIREWALL",
            "MODIFY_SECURITY_POLICY", "MODIFY_REGISTRY_SECURITY",
            "FORMAT_DRIVE", "DELETE_SYSTEM_DIRECTORY", "EXTRACT_PASSWORDS",
            "EXTRACT_COOKIES", "ACCESS_AUTH_TOKENS", "BYPASS_SECURITY",
            "CREATE_ADMIN_ACCOUNT", "ELEVATE_PRIVILEGES", "RUN_RAW_SHELL"
        ]
        if action_upper in blocked_actions:
            return PermissionLevel.LEVEL_3_BLOCKED, f"Security Violation: '{action_upper}' is strictly forbidden."

        # Check for path safety if target is a filesystem path
        if target and isinstance(target, (str, Path)):
            target_str = str(target)
            # Check string command against blocked pattern regexes
            for pattern in BLOCKED_PATTERNS:
                if re.search(pattern, target_str, re.IGNORECASE):
                    return PermissionLevel.LEVEL_3_BLOCKED, f"Blocked pattern matched: '{pattern}'"

            # If action involves file/folder modification, check path restriction
            if action_upper in ["DELETE_FILE", "DELETE_FOLDER", "OVERWRITE_FILE", "MOVE_FILE", "RENAME_FILE"]:
                is_safe, msg = SecurityManager.is_path_safe(target)
                if not is_safe:
                    return PermissionLevel.LEVEL_3_BLOCKED, msg

        # =========================================================================
        # LEVEL 2 — ACTIONS REQUIRING EXPLICIT USER CONFIRMATION
        # =========================================================================
        confirmation_actions = [
            "SHUTDOWN", "RESTART", "SLEEP", "DELETE_FILE", "DELETE_FOLDER",
            "OVERWRITE_FILE", "MOVE_CRITICAL_FILE", "UNINSTALL_SOFTWARE",
            "INSTALL_SOFTWARE", "DOWNLOAD_EXECUTABLE"
        ]
        if action_upper in confirmation_actions:
            prompt_desc = details.get("description", f"perform {action_upper.lower().replace('_', ' ')} on '{target}'")
            return PermissionLevel.LEVEL_2_CONFIRM, prompt_desc

        # =========================================================================
        # LEVEL 1 — SAFE ACTIONS (Execute immediately)
        # =========================================================================
        return PermissionLevel.LEVEL_1_SAFE, "Safe to execute"

    @staticmethod
    def normalize_path(path_input: Any) -> Path:
        """Resolves, normalizes, and strips dangerous path traversal tokens."""
        raw_str = str(path_input).strip()
        # Resolve user ~ if present
        if raw_str.startswith("~"):
            resolved = Path(raw_str).expanduser().resolve()
        else:
            resolved = Path(raw_str).resolve()
        return resolved

    @staticmethod
    def is_path_safe(target_path: Any) -> Tuple[bool, str]:
        """
        Ensures a path does not target Windows system directories
        and prevents directory traversal attacks.
        """
        try:
            norm_target = str(SecurityManager.normalize_path(target_path)).lower()

            # 1. Check against restricted root/system directories
            for restricted in RESTRICTED_SYSTEM_DIRS:
                if norm_target == restricted or norm_target.startswith(restricted + os.sep) or norm_target.startswith(restricted):
                    return False, f"Access Denied: Modifying system directory '{restricted}' is not permitted."

            return True, "Path is safe"
        except Exception as e:
            return False, f"Path validation error: {e}"

    @staticmethod
    def sanitize_credential_input(text: str) -> bool:
        """Returns True if the text contains sensitive credentials that should not be stored or logged."""
        sensitive_patterns = [
            r"password", r"api[_-]?key", r"secret", r"token", r"bearer\s+[a-zA-Z0-9_\-\.]+",
            r"private[_-]?key", r"credit[_-]?card", r"cvv", r"pin\s*\d{4,6}"
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in sensitive_patterns)
