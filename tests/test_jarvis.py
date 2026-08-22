"""
tests/test_jarvis.py
Automated test suite verifying the complete JARVIS system:
Wake word, Language, Memory, Reminders, Notes, Laptop Controls, and Security Guard.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import config
from jarvis.core.memory import MemoryManager
from jarvis.core.brain import AIBrain
from jarvis.core.wake_word import WakeWordDetector
from jarvis.core.language import LanguageManager
from jarvis.actions.safety import SafetyGuard
from jarvis.actions.system_actions import SystemActions
from jarvis.actions.computer_actions import ComputerActions
from jarvis.core.intent_router import IntentRouter


class MockTTS:
    def speak(self, text: str):
        pass


class TestJarvisCore(unittest.TestCase):

    def setUp(self):
        self.memory = MemoryManager()
        self.brain = AIBrain()
        self.tts = MockTTS()
        self.wake_detector = WakeWordDetector()
        self.language = LanguageManager(self.memory)
        self.router = IntentRouter(self.memory, self.brain, self.tts)

    def test_wake_word_detection(self):
        """Test exact and prefix wake-word detection."""
        has_wake, remaining = self.wake_detector.check_wake_word("hey jarvis")
        self.assertTrue(has_wake)
        self.assertIsNone(remaining)

        has_wake, remaining = self.wake_detector.check_wake_word("hey jarvis open chrome")
        self.assertTrue(has_wake)
        self.assertEqual(remaining, "open chrome")

        has_wake, remaining = self.wake_detector.check_wake_word("open notepad")
        self.assertFalse(has_wake)

    def test_language_detection(self):
        """Test Hindi, Hinglish, and English detection."""
        lang_hi = self.language.detect_language("Chrome kholo")
        self.assertIn(lang_hi, [config.LANG_HI, config.LANG_HINGLISH])

        lang_en = self.language.detect_language("open google chrome browser")
        self.assertEqual(lang_en, config.LANG_EN)

    def test_memory_secret_protection(self):
        """Test that sensitive passwords and API keys are blocked from storage."""
        blocked_1 = self.memory.set_preference("my_pass", "secretpassword123")
        self.assertFalse(blocked_1)

        blocked_2 = self.memory.set_preference("api_key", "sk-1234567890")
        self.assertFalse(blocked_2)

        allowed = self.memory.set_preference("favorite_color", "cyan")
        self.assertTrue(allowed)

    def test_reminders_and_notes(self):
        """Test creating and retrieving local reminders and notes."""
        note_id = self.memory.add_note("Meeting", "Complete AI project tomorrow")
        self.assertTrue(note_id > 0)
        notes = self.memory.get_all_notes()
        self.assertTrue(len(notes) > 0)

        success, details = self.router.reminders.parse_and_create("remind me in 10 minutes to submit assignment")
        self.assertTrue(success)

    def test_safety_blocked_commands(self):
        """Test that dangerous system commands are blocked."""
        unsafe_cmd = "shutdown /s /t 0"
        is_safe, msg = SafetyGuard.is_command_safe(unsafe_cmd)
        self.assertFalse(is_safe)
        self.assertIn("blocked", msg.lower())

    def test_safety_restricted_paths(self):
        """Test that Windows system directories cannot be altered."""
        system_dir = Path("C:/Windows/System32/evil_folder")
        is_safe, _ = SafetyGuard.is_path_safe(system_dir)
        self.assertFalse(is_safe)

    def test_system_telemetry(self):
        """Test real-time CPU, RAM, Battery, and Network telemetry."""
        metrics = SystemActions.get_system_metrics()
        self.assertIn("cpu", metrics)
        self.assertIn("ram", metrics)
        self.assertIn("battery", metrics)
        self.assertIn("network", metrics)

    def test_hindi_intent_routing(self):
        """Test Hindi / Hinglish intent execution."""
        success, msg, _ = self.router.process_command("Chrome kholo")
        self.assertTrue(success)
        self.assertIn("Chrome", msg)

    def test_file_search_and_operations(self):
        """Test local file search engine and directory security."""
        from jarvis.actions.file_actions import FileActions
        results = FileActions.search_files("main", extension="py")
        self.assertTrue(len(results) > 0)
        self.assertTrue(any("main.py" in r["name"] for r in results))

    def test_multi_step_planner(self):
        """Test multi-step composite task detection."""
        from jarvis.core.planner import TaskPlanner
        planner = TaskPlanner(self.memory, self.tts)
        is_multi = planner.is_multi_step_request("Find my Python project and open it in VS Code")
        self.assertTrue(is_multi)

    def test_security_manager_3_tiers(self):
        """Test 3-tier permission validator."""
        from jarvis.core.security_manager import SecurityManager, PermissionLevel
        # Level 1 Safe
        perm_1, _ = SecurityManager.validate_action("OPEN_APPLICATION", "chrome")
        self.assertEqual(perm_1, PermissionLevel.LEVEL_1_SAFE)

        # Level 2 Confirmation
        perm_2, _ = SecurityManager.validate_action("SHUTDOWN")
        self.assertEqual(perm_2, PermissionLevel.LEVEL_2_CONFIRM)

        # Level 3 Blocked
        perm_3, _ = SecurityManager.validate_action("DISABLE_ANTIVIRUS")
        self.assertEqual(perm_3, PermissionLevel.LEVEL_3_BLOCKED)


if __name__ == "__main__":
    unittest.main()
