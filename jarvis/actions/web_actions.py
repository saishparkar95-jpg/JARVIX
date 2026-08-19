"""
jarvis/actions/web_actions.py
Web automation actions: Searching Google, YouTube, News, Weather, and opening websites.
"""

import webbrowser
import urllib.parse
from typing import Tuple
import config


POPULAR_SITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "chatgpt": "https://chat.openai.com",
    "gemini": "https://gemini.google.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "gmail": "https://mail.google.com",
    "maps": "https://maps.google.com",
    "spotify": "https://open.spotify.com"
}


class WebActions:
    """Handles browser searches, news, weather, and URL navigation."""

    @staticmethod
    def search_google(query: str) -> Tuple[bool, str]:
        """Performs a Google web search."""
        if not query:
            return False, "Search query is empty."

        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        try:
            webbrowser.open(url)
            return True, query
        except Exception as e:
            return False, f"Failed to perform search: {e}"

    @staticmethod
    def search_youtube(query: str) -> Tuple[bool, str]:
        """Performs a YouTube video search."""
        if not query:
            return False, "YouTube search query is empty."

        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        try:
            webbrowser.open(url)
            return True, query
        except Exception as e:
            return False, f"Failed to search YouTube: {e}"

    @staticmethod
    def search_weather(location: str = "") -> Tuple[bool, str]:
        """Searches current weather for location."""
        query = f"weather in {location}" if location else "current weather"
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        try:
            webbrowser.open(url)
            return True, location or "your location"
        except Exception as e:
            return False, f"Failed to search weather: {e}"

    @staticmethod
    def search_news(topic: str = "") -> Tuple[bool, str]:
        """Searches latest news."""
        query = f"latest {topic} news" if topic else "latest news"
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}&tbm=nws"
        try:
            webbrowser.open(url)
            return True, topic or "top headlines"
        except Exception as e:
            return False, f"Failed to search news: {e}"

    @staticmethod
    def open_website(target: str) -> Tuple[bool, str]:
        """Opens a website URL or known service."""
        target_clean = target.lower().strip()

        if target_clean in POPULAR_SITES:
            url = POPULAR_SITES[target_clean]
        elif target_clean.startswith("http://") or target_clean.startswith("https://"):
            url = target_clean
        elif "." in target_clean:
            url = f"https://{target_clean}"
        else:
            return WebActions.search_google(target)

        try:
            webbrowser.open(url)
            return True, target
        except Exception as e:
            return False, f"Failed to open website: {e}"
