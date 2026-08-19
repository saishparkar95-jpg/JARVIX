"""
jarvis/core/brain.py
AI Brain interface providing LLM reasoning (OpenAI) with an offline fallback.
"""

from typing import List, Dict
import config

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AIBrain:
    """Provides LLM intelligence and conversational capabilities for JARVIS."""

    def __init__(self):
        self.client = None
        self.provider = config.AI_PROVIDER
        self.model = config.AI_MODEL
        self._init_client()

    def _init_client(self):
        """Initializes the OpenAI client if an API key is configured."""
        if config.OPENAI_API_KEY and OpenAI:
            try:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            except Exception as e:
                print(f"[\033[93mBrain Notice\033[0m] AI Brain client initialization notice: {e}")
                self.client = None

    def ask(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Sends the user prompt to the configured LLM brain.
        Falls back gracefully to built-in conversational responses if offline or without API key.
        """
        if self.client:
            try:
                system_prompt = (
                    f"You are {config.ASSISTANT_NAME}, a highly intelligent, polite, and helpful "
                    f"AI desktop assistant for Windows. Address the user as {config.USER_NAME}. "
                    f"Keep your spoken responses concise, clear, natural, and helpful (typically 1-3 sentences), "
                    f"as your response will be read aloud by a Text-to-Speech engine."
                )

                messages = [{"role": "system", "content": system_prompt}]

                if conversation_history:
                    messages.extend(conversation_history)

                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=200,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                print(f"[\033[93mAI Brain API Error\033[0m]: {e}")
                return self._offline_fallback(prompt)
        else:
            return self._offline_fallback(prompt)

    def _offline_fallback(self, prompt: str) -> str:
        """Built-in conversational answers when operating in offline/no-API-key mode."""
        prompt_lower = prompt.lower()

        if any(w in prompt_lower for w in ["who are you", "what is your name"]):
            return f"I am {config.ASSISTANT_NAME}, your personal desktop AI assistant for Windows."

        if any(w in prompt_lower for w in ["how are you", "how's it going"]):
            return f"I am operating at peak efficiency, {config.USER_NAME}. How may I assist you today?"

        if any(w in prompt_lower for w in ["hello", "hi", "hey"]):
            return f"Greetings {config.USER_NAME}. I am ready for your commands."

        if any(w in prompt_lower for w in ["thank you", "thanks"]):
            return f"Always at your service, {config.USER_NAME}."

        if any(w in prompt_lower for w in ["what can you do", "help", "commands"]):
            return (
                f"I can open applications like Chrome, VS Code, and Notepad, search the web, "
                f"tell you the current time and date, take screenshots, create folders, and answer questions."
            )

        return (
            f"I have processed your query, {config.USER_NAME}. To enable full open-domain AI reasoning, "
            f"please provide an OPENAI_API_KEY in your .env file."
        )
