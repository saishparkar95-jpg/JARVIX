"""
jarvis/core/brain.py
AI Brain interface providing LLM reasoning (OpenAI) with high-speed intelligent fallback.
"""

import json
import math
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Optional
import config

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AIBrain:
    """Provides LLM intelligence, fast computation, and knowledge retrieval for JARVIS."""

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
        Falls back to fast built-in AI reasoning & knowledge retrieval if offline or without API key.
        """
        if not prompt or not prompt.strip():
            return "How can I assist you?"

        # 1. Try OpenAI if API key configured
        if self.client:
            try:
                system_prompt = (
                    f"You are {config.ASSISTANT_NAME}, a super-intelligent, concise, and helpful "
                    f"AI desktop assistant for Windows. Address the user as {config.USER_NAME}. "
                    f"Keep responses brief, natural, and clear (typically 1 to 2 sentences) "
                    f"as your response will be read aloud by Text-to-Speech."
                )

                messages = [{"role": "system", "content": system_prompt}]
                if conversation_history:
                    messages.extend(conversation_history[-4:])
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=150,
                    temperature=0.6
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                print(f"[\033[93mAI Brain API Error\033[0m]: {e}")

        # 2. Intelligent Built-in AI Reasoning & Calculation
        return self._intelligent_fallback(prompt)

    def _intelligent_fallback(self, prompt: str) -> str:
        """High-speed built-in AI reasoning engine covering math, facts, concepts, and dialogue."""
        cleaned = prompt.strip()
        lower = cleaned.lower()

        # Math calculations
        math_ans = self._calculate_math(lower)
        if math_ans:
            return math_ans

        # Greetings & Persona
        if any(w in lower for w in ["who are you", "what is your name", "who made you", "tum kaun ho"]):
            return f"I am {config.ASSISTANT_NAME}, your personal desktop AI assistant. I am designed to assist you with system tasks, productivity, and queries."

        if any(w in lower for w in ["how are you", "how are u", "kaise ho"]):
            return f"I am functioning at maximum capacity and ready to assist, {config.USER_NAME}."

        if any(w in lower for w in ["hello", "hi", "hey jarvis", "namaste", "suno"]):
            return f"Hello {config.USER_NAME}! How can I help you right now?"

        if any(w in lower for w in ["thank you", "thanks", "dhanyawad", "shukriya"]):
            return f"You're very welcome, {config.USER_NAME}. It is always a pleasure."

        if any(w in lower for w in ["tell me a joke", "joke sunao", "make me laugh"]):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "Why did the computer catch a cold? It left its Windows open.",
                "There are 10 types of people in the world: those who understand binary, and those who don't."
            ]
            import random
            return random.choice(jokes)

        if any(w in lower for w in ["what can you do", "help me", "kya kar sakte ho"]):
            return (
                f"I can control your volume, open apps and websites, take screenshots, manage notes, "
                f"check battery and system stats, solve math, and answer knowledge questions."
            )

        # Knowledge search via Wikipedia REST & Fulltext Search
        wiki_ans = self._lookup_knowledge(cleaned)
        if wiki_ans:
            return wiki_ans

        return f"I have noted your command, {config.USER_NAME}. Would you like me to search Google for '{cleaned}'?"

    def _calculate_math(self, text: str) -> Optional[str]:
        """Evaluates arithmetic expressions safely."""
        # Replace spoken words with math operators
        expr = text.replace("plus", "+").replace("minus", "-").replace("multiplied by", "*")
        expr = expr.replace("into", "*").replace("times", "*").replace("divided by", "/").replace("over", "/")
        expr = expr.replace("calculate", "").replace("what is", "").replace("solve", "").replace("kitna hota hai", "")
        
        # Match percentage: e.g. "15% of 500" or "15 percent of 500"
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+of\s+(\d+(?:\.\d+)?)", expr)
        if pct_match:
            p, val = float(pct_match.group(1)), float(pct_match.group(2))
            res = (p / 100.0) * val
            return f"{p}% of {val} is {res:g}."

        # Match arithmetic like: 25 * 4, 100 + 50, (40 / 5) * 2
        clean_expr = re.sub(r"[^0-9\+\-\*\/\.\(\)\s]", "", expr).strip()
        if clean_expr and any(op in clean_expr for op in ["+", "-", "*", "/"]):
            try:
                # Disallow double underscores or letters
                result = eval(clean_expr, {"__builtins__": None}, {"math": math})
                if isinstance(result, (int, float)):
                    return f"The answer is {result:g}."
            except Exception:
                pass
        return None

    def _lookup_knowledge(self, query: str) -> Optional[str]:
        """Fetches instantaneous 1-2 sentence summary from Wikipedia using direct and fulltext search."""
        import ssl
        ctx = ssl._create_unverified_context()

        # Clean prefix phrases using regex boundaries
        cleaned_topic = re.sub(
            r'^(what is the definition of|what is an|what is a|what is|what are|who invented|who discovered|who created|who wrote|who founded|who was|who is|tell me about|explain|define|what do you know about|why is|why do|how does|how do|where is|when was)\s+(?:the\s+|a\s+|an\s+)?',
            '',
            query,
            flags=re.IGNORECASE
        )
        cleaned_topic = re.sub(r'\s+(kya hai|kaun hai|batao)$', '', cleaned_topic, flags=re.IGNORECASE)
        topic = cleaned_topic.strip(" ?.,!")

        if not topic or len(topic) < 2:
            return None

        # 1. Direct candidate titles
        candidates = [
            topic.capitalize().replace(" ", "_"),
            topic.title().replace(" ", "_"),
            topic.replace(" ", "_")
        ]

        for cand in candidates:
            try:
                encoded = urllib.parse.quote(cand)
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
                req = urllib.request.Request(url, headers={"User-Agent": "JarvisAI/1.2 (Windows Desktop Assistant)"})
                with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        extract = data.get("extract")
                        if extract and data.get("type", "") != "disambiguation":
                            sentences = re.split(r'(?<=[.!?])\s+', extract)
                            return " ".join(sentences[:2])
            except Exception:
                continue

        # 2. Full-text search fallback for complex questions
        try:
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&utf8=1"
            req = urllib.request.Request(search_url, headers={"User-Agent": "JarvisAI/1.2 (Windows Desktop Assistant)"})
            with urllib.request.urlopen(req, context=ctx, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("query", {}).get("search", [])
                    if results:
                        top_title = results[0]["title"]
                        s_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(top_title.replace(' ', '_'))}"
                        s_req = urllib.request.Request(s_url, headers={"User-Agent": "JarvisAI/1.2 (Windows Desktop Assistant)"})
                        with urllib.request.urlopen(s_req, context=ctx, timeout=2.5) as s_resp:
                            if s_resp.status == 200:
                                s_data = json.loads(s_resp.read().decode("utf-8"))
                                extract = s_data.get("extract")
                                if extract:
                                    sentences = re.split(r'(?<=[.!?])\s+', extract)
                                    return " ".join(sentences[:2])
        except Exception:
            pass

        return None
