"""
Small wrapper around the Gemini API.

The rest of the app only calls `complete(system_prompt, user_prompt)` and gets a
string back. On any failure it returns "" so the agent can switch to its offline
fallback instead of crashing.
"""

import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-flash-lite-latest"


class GeminiClient:
    def __init__(self, api_key: str, model_name: Optional[str] = None, temperature: float = 0.2):
        # Imported here so offline mode works even if google-genai is missing.
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        self.temperature = temperature

    def complete(self, system_prompt: str, user_prompt: str, retries: int = 1) -> str:
        from google.genai import types

        for attempt in range(retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=self.temperature,
                    ),
                )
                return response.text or ""
            except Exception as err:  # network errors, rate limits, blocked output
                log.warning("Gemini call failed (attempt %d): %s", attempt + 1, err)
                if attempt < retries:
                    # Rate limits (429) usually clear after a short wait.
                    time.sleep(5 if "429" in str(err) else 1)
        return ""


def get_client(offline: bool = False) -> Optional[GeminiClient]:
    """Return a Gemini client, or None when offline or when no API key is set."""
    if offline:
        return None
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        log.info("No GEMINI_API_KEY found, running in offline mode")
        return None
    try:
        return GeminiClient(api_key)
    except Exception as err:
        log.warning("Could not start Gemini client, running offline: %s", err)
        return None
