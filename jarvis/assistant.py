"""
jarvis/assistant.py
Main JARVIS AI Assistant coordinator.
Coordinates speech recognition, wake-word activation, state transitions, intent routing, and memory.
"""

import sys
from datetime import datetime
import config
from jarvis.core.tts import TTSEngine
from jarvis.core.stt import STTEngine
from jarvis.core.wake_word import WakeWordDetector
from jarvis.core.memory import MemoryManager
from jarvis.core.brain import AIBrain
from jarvis.core.intent_router import IntentRouter


class JarvisAssistant:
    """The central orchestrator for JARVIS desktop assistant."""

    def __init__(self):
        print("\033[96m" + "=" * 60)
        print(f"   🤖 {config.ASSISTANT_NAME} Personal Voice Assistant v1.1   ")
        print(f"      Wake Word: \"{config.WAKE_WORDS[0].title()}\" | Mode: {config.INPUT_MODE.upper()}      ")
        print("=" * 60 + "\033[0m")

        self.state = config.STATE_IDLE
        self.memory = MemoryManager()
        self.tts = TTSEngine()
        self.stt = STTEngine()
        self.wake_detector = WakeWordDetector()
        self.brain = AIBrain()
        self.router = IntentRouter(self.memory, self.brain, self.tts)

    def set_state(self, new_state: str, details: str = ""):
        """Updates and prints the current assistant state."""
        self.state = new_state
        state_colors = {
            config.STATE_IDLE: "\033[90m",       # Gray
            config.STATE_LISTENING: "\033[92m",  # Green
            config.STATE_THINKING: "\033[93m",   # Yellow
            config.STATE_EXECUTING: "\033[94m",  # Blue
            config.STATE_SPEAKING: "\033[95m",   # Magenta
            config.STATE_ERROR: "\033[91m",      # Red
        }
        color = state_colors.get(new_state, "\033[0m")
        suffix = f" - {details}" if details else ""
        print(f"{color}[STATE: {new_state}]{suffix}\033[0m")

    def startup_greeting(self):
        """Greets the user upon startup based on time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = f"Good morning {config.USER_NAME}."
        elif 12 <= hour < 18:
            greeting = f"Good afternoon {config.USER_NAME}."
        else:
            greeting = f"Good evening {config.USER_NAME}."

        wake_tip = f"Say \"{config.WAKE_WORDS[0].title()}\" to activate me anytime."
        welcome_message = f"{greeting} {config.ASSISTANT_NAME} is online. {wake_tip}"
        
        self.set_state(config.STATE_SPEAKING)
        self.memory.log_conversation(config.ASSISTANT_NAME, welcome_message)
        self.tts.speak(welcome_message)
        self.set_state(config.STATE_IDLE, f"Waiting for \"{config.WAKE_WORDS[0].title()}\"")

    def run(self):
        """Starts the main assistant interaction loop with wake-word support."""
        self.startup_greeting()

        running = True
        while running:
            try:
                # ----------------------------------------------------
                # 1. IDLE STATE: Listen for Wake Word ("Hey Jarvis")
                # ----------------------------------------------------
                if config.INPUT_MODE == "voice":
                    print(f"\r\033[90m[JARVIS is in standby. Say \"{config.WAKE_WORDS[0].title()}\"...]\033[0m", end="", flush=True)

                detected, inline_command = self.stt.listen_for_wake_word(self.wake_detector)

                if not detected:
                    continue

                # ----------------------------------------------------
                # 2. LISTENING STATE: Wake Word Triggered!
                # ----------------------------------------------------
                print()  # New line
                self.set_state(config.STATE_LISTENING, "Wake word detected!")
                self.wake_detector.play_activation_sound()

                # If the user already provided the command inline (e.g. "Hey Jarvis open Chrome")
                if inline_command:
                    command = inline_command
                    print(f"\033[94m[{config.USER_NAME} (Voice)]\033[0m: {command}")
                else:
                    # Otherwise, listen for their command
                    command = self.stt.listen_command()

                if not command:
                    self.set_state(config.STATE_IDLE, "No speech detected, returning to standby")
                    continue

                # ----------------------------------------------------
                # 3. Handle Interruption / Quick Cancel
                # ----------------------------------------------------
                if command.lower() in ["stop", "cancel", "nevermind", "dismiss"]:
                    self.set_state(config.STATE_SPEAKING)
                    self.tts.speak(f"Action cancelled, {config.USER_NAME}.")
                    self.set_state(config.STATE_IDLE)
                    continue

                # ----------------------------------------------------
                # 4. THINKING & EXECUTING: Process Command
                # ----------------------------------------------------
                self.set_state(config.STATE_THINKING, f"Analyzing \"{command}\"")
                self.memory.log_conversation(config.USER_NAME, command)

                self.set_state(config.STATE_EXECUTING)
                success, response_text, should_exit = self.router.process_command(command)

                # ----------------------------------------------------
                # 5. SPEAKING STATE: Deliver Audio Response
                # ----------------------------------------------------
                if response_text:
                    self.set_state(config.STATE_SPEAKING)
                    self.memory.log_conversation(config.ASSISTANT_NAME, response_text)
                    self.tts.speak(response_text)

                # ----------------------------------------------------
                # 6. RETURN TO IDLE (or exit if requested)
                # ----------------------------------------------------
                if should_exit:
                    running = False
                else:
                    self.set_state(config.STATE_IDLE, f"Waiting for \"{config.WAKE_WORDS[0].title()}\"")

            except KeyboardInterrupt:
                print("\n\n\033[93m[Interrupted by user. Exiting...]\033[0m")
                self.set_state(config.STATE_SPEAKING)
                self.tts.speak(f"Shutting down. Goodbye {config.USER_NAME}.")
                running = False
            except Exception as e:
                self.set_state(config.STATE_ERROR, str(e))
                print(f"\033[91m[Error in assistant loop: {e}]\033[0m")
                self.set_state(config.STATE_IDLE)
