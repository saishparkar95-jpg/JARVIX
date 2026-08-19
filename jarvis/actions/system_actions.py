import os
import socket
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any
import pyautogui
from PIL import Image
import psutil
import config
from jarvis.actions.safety import SafetyGuard


class SystemActions:
    """Handles safe system information queries and file/desktop utilities."""

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Returns real-time system metrics (CPU, RAM, Battery, Network)."""
        cpu_percent = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        
        battery_pct = battery.percent if battery else 100
        is_charging = battery.power_plugged if battery else True
        
        # Check network connectivity
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=1):
                network_status = "ONLINE"
        except OSError:
            network_status = "OFFLINE"

        return {
            "cpu": cpu_percent,
            "ram": ram.percent,
            "battery": battery_pct,
            "charging": is_charging,
            "network": network_status
        }

    @staticmethod
    def get_current_time() -> str:
        """Returns formatted current time."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        return f"The current time is {time_str}, {config.USER_NAME}."

    @staticmethod
    def get_current_date() -> str:
        """Returns formatted current date."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return f"Today is {date_str}, {config.USER_NAME}."

    @staticmethod
    def take_screenshot() -> Tuple[bool, str]:
        """
        Takes a desktop screenshot and saves it safely in the Screenshots directory.
        """
        try:
            config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            file_path = config.SCREENSHOTS_DIR / filename

            # Take screenshot using pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(str(file_path))

            return True, f"Screenshot captured successfully and saved to {file_path.name} in your Screenshots folder."
        except Exception as e:
            return False, f"Failed to capture screenshot: {e}"

    @staticmethod
    def create_folder(folder_name: str, target_dir: Path = None, tts_engine=None) -> Tuple[bool, str]:
        """
        Safely creates a new directory in the workspace or desktop.
        Validates target path against safety rules.
        """
        if not folder_name:
            return False, "Folder name was not specified."

        # Sanitize folder name
        cleaned_name = "".join(c for c in folder_name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not cleaned_name:
            return False, "Invalid folder name provided."

        if target_dir is None:
            # Default to current user's desktop or base dir
            desktop_path = Path.home() / "Desktop"
            target_dir = desktop_path if desktop_path.exists() else config.BASE_DIR

        new_folder_path = target_dir / cleaned_name

        # Safety validation
        is_safe, msg = SafetyGuard.is_path_safe(new_folder_path)
        if not is_safe:
            return False, msg

        # Check user confirmation
        if config.REQUIRE_CONFIRMATION:
            action_desc = f"create a new folder named '{cleaned_name}' at '{target_dir}'"
            if not SafetyGuard.request_confirmation(action_desc, tts_engine=tts_engine):
                return False, "Folder creation cancelled by user."

        try:
            new_folder_path.mkdir(parents=True, exist_ok=True)
            return True, f"Folder '{cleaned_name}' created successfully at {target_dir}."
        except Exception as e:
            return False, f"Error creating folder: {e}"
