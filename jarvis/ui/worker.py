"""
jarvis/ui/worker.py
Non-blocking QThread background workers for continuous hands-free voice assistance and telemetry.
"""

import time
from PySide6.QtCore import QThread, Signal
import config
from jarvis.core.memory import MemoryManager
from jarvis.core.tts import TTSEngine
from jarvis.core.stt import STTEngine
from jarvis.core.wake_word import WakeWordDetector
from jarvis.core.brain import AIBrain
from jarvis.core.intent_router import IntentRouter
from jarvis.actions.system_actions import SystemActions


class VoiceWorker(QThread):
    """Background worker handling 100% hands-free voice capture, intent execution, and audio output."""

    state_changed = Signal(str, str)             # (state, details)
    user_spoke = Signal(str)                     # (user_transcript)
    jarvis_replied = Signal(str)                 # (assistant_response)
    system_log = Signal(str)                     # (log_message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True
        self.is_paused = False
        self.manual_mic_triggered = False

        self.memory = MemoryManager()
        self.tts = TTSEngine()
        self.stt = STTEngine()
        self.wake_detector = WakeWordDetector()
        self.brain = AIBrain()
        self.router = IntentRouter(self.memory, self.brain, self.tts)

    def run(self):
        """Continuous hands-free voice loop (Google Assistant style)."""
        self.state_changed.emit(config.STATE_IDLE, f"Standby. Just say \"{config.WAKE_WORDS[0].title()}\" or your command")

        while self.is_running:
            try:
                if self.is_paused:
                    time.sleep(0.2)
                    continue

                # Continuous stream listen: triggers automatically when speech is heard
                spoken_text = self.stt.listen_continuous(silence_threshold=0.006)

                if not spoken_text or not self.is_running:
                    continue

                print(f"\n\033[94m[Heard Speech]\033[0m: '{spoken_text}'")

                # Check if speech contains wake word (e.g., "Hey Jarvis open Chrome" or "Jarvis what is the time")
                has_wake, extracted_cmd = self.wake_detector.check_wake_word(spoken_text)

                command_to_run = None

                if has_wake:
                    self.state_changed.emit(config.STATE_LISTENING, "Wake word detected!")
                    self.wake_detector.play_activation_sound()
                    command_to_run = extracted_cmd if extracted_cmd else self.stt.listen_continuous(silence_threshold=0.006)
                elif self.manual_mic_triggered:
                    self.manual_mic_triggered = False
                    self.state_changed.emit(config.STATE_LISTENING, "Listening...")
                    self.wake_detector.play_activation_sound()
                    command_to_run = spoken_text
                else:
                    # Also accept direct commands (like "Chrome kholo", "What is the time", "Battery kitni hai")
                    # If direct command matches a recognized intent
                    command_to_run = spoken_text

                if not command_to_run or not command_to_run.strip():
                    self.state_changed.emit(config.STATE_IDLE, f"Standby. Just say \"{config.WAKE_WORDS[0].title()}\"")
                    continue

                # 3. Interruption / Quick Cancel
                if command_to_run.lower() in ["stop", "cancel", "dismiss", "nevermind", "ruko", "band karo"]:
                    self.state_changed.emit(config.STATE_SPEAKING, "Cancelled")
                    self.tts.speak(f"Action cancelled, {config.USER_NAME}.")
                    self.state_changed.emit(config.STATE_IDLE, f"Standby. Say \"{config.WAKE_WORDS[0].title()}\"")
                    continue

                # 4. Thinking & Executing
                self.user_spoke.emit(command_to_run)
                self.memory.log_conversation(config.USER_NAME, command_to_run)

                self.state_changed.emit(config.STATE_THINKING, f"Analyzing: \"{command_to_run}\"")
                time.sleep(0.1)

                self.state_changed.emit(config.STATE_EXECUTING, "Executing action...")
                success, response_text, should_exit = self.router.process_command(command_to_run)

                # 5. Speaking response
                if response_text:
                    self.state_changed.emit(config.STATE_SPEAKING, "Speaking...")
                    self.jarvis_replied.emit(response_text)
                    self.memory.log_conversation(config.ASSISTANT_NAME, response_text)
                    self.tts.speak(response_text)

                if should_exit:
                    self.is_running = False
                    break

                self.state_changed.emit(config.STATE_IDLE, f"Standby. Just say \"{config.WAKE_WORDS[0].title()}\"")

            except Exception as e:
                self.state_changed.emit(config.STATE_ERROR, str(e))
                time.sleep(0.5)
                self.state_changed.emit(config.STATE_IDLE, f"Standby. Say \"{config.WAKE_WORDS[0].title()}\"")

    def trigger_manual_listen(self):
        """Manual microphone button trigger."""
        self.manual_mic_triggered = True

    def pause_listening(self):
        """Pauses microphone monitoring."""
        self.is_paused = True
        self.state_changed.emit(config.STATE_IDLE, "Paused")

    def resume_listening(self):
        """Resumes microphone monitoring."""
        self.is_paused = False
        self.state_changed.emit(config.STATE_IDLE, f"Standby. Say \"{config.WAKE_WORDS[0].title()}\"")

    def stop(self):
        """Stops the voice worker thread."""
        self.is_running = False
        self.stt.close()
        self.wait(1000)


class SystemMonitorWorker(QThread):
    """Polls CPU, RAM, Battery, and Network status periodically."""

    metrics_updated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                metrics = SystemActions.get_system_metrics()
                self.metrics_updated.emit(metrics)
            except Exception:
                pass
            time.sleep(2.0)

    def stop(self):
        self.is_running = False
        self.wait(500)
