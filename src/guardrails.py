"""
Guardrails for the assistant.

1. check_request   - runs before anything else and blocks bad input.
2. validate_profile - cleans the taste profile the planner produced.
3. verify_answer   - checks the final answer only uses songs we actually retrieved.
"""

import difflib
import json
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

MAX_REQUEST_CHARS = 300

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|rules|prompts?)",
    r"disregard (all |the )?(previous|prior|above)",
    r"system prompt",
    r"you are now",
    r"act as (a|an) ",
    r"reveal (your|the) (instructions|prompt|rules)",
    r"api[_ ]?key",
]

MUSIC_WORDS = {
    "music", "song", "songs", "playlist", "track", "tracks", "listen", "listening",
    "artist", "band", "genre", "beat", "beats", "tune", "tunes", "album", "vibe",
    "vibes", "sound", "sounds", "play", "recommend",
}

# Common ways people write genres and moods that are not spelled like the catalog.
GENRE_ALIASES = {
    "hip hop": "hip-hop", "hiphop": "hip-hop", "rap": "hip-hop", "rnb": "r&b",
    "r and b": "r&b", "lo-fi": "lofi", "lo fi": "lofi", "electronic": "edm",
    "dance": "edm", "indie": "indie pop", "reggaeton": "latin", "heavy metal": "metal",
}
MOOD_ALIASES = {
    "calm": "peaceful", "upbeat": "happy", "cheerful": "happy", "angry": "aggressive",
    "melancholic": "sad", "melancholy": "sad", "relaxing": "relaxed", "hype": "energetic",
    "excited": "energetic", "focus": "focused", "dark": "moody", "love": "romantic",
}

UNIT_FEATURES = {"energy", "valence", "danceability", "acousticness"}
ALLOWED_KEYS = UNIT_FEATURES | {"genre", "mood", "mood_tag", "tempo_bpm", "popularity", "release_decade"}


def check_request(text: str, known_words: Iterable[str] = ()) -> Tuple[bool, str]:
    """Return (ok, reason). known_words are extra on-topic words, such as guide keywords."""
    if text is None or not text.strip():
        return False, "The request is empty. Describe the music you want, like 'calm songs for studying'."
    text = text.strip()
    if len(text) > MAX_REQUEST_CHARS:
        return False, f"The request is too long ({len(text)} characters, limit {MAX_REQUEST_CHARS})."
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return False, "The request looks like an attempt to change the assistant's instructions, so it was blocked."
    words = set(re.findall(r"[a-z0-9&'-]+", lowered))
    if not words & (MUSIC_WORDS | set(known_words)):
        return False, "This does not look like a music request. Try describing a mood, activity or genre."
    return True, "ok"


def _match_label(value: str, allowed: Set[str], aliases: Dict[str, str]) -> Optional[str]:
    value = value.strip().lower()
    if value in allowed:
        return value
    if aliases.get(value) in allowed:
        return aliases[value]
    close = difflib.get_close_matches(value, sorted(allowed), n=1, cutoff=0.75)
    return close[0] if close else None


def validate_profile(raw: Dict, genres: Set[str], moods: Set[str]) -> Tuple[Dict, List[str]]:
    """Return a cleaned profile plus a list of every fix that was made."""
    profile: Dict = {}
    fixes: List[str] = []

    for key, value in (raw or {}).items():
        if key not in ALLOWED_KEYS:
            fixes.append(f"dropped unknown field '{key}'")
            continue
        if value is None or value == "":
            continue

        if key in ("genre", "mood"):
            allowed, aliases = (genres, GENRE_ALIASES) if key == "genre" else (moods, MOOD_ALIASES)
            matched = _match_label(str(value), allowed, aliases)
            if matched is None:
                fixes.append(f"removed {key} '{value}' (not in catalog)")
            else:
                if matched != str(value).strip().lower():
                    fixes.append(f"mapped {key} '{value}' -> '{matched}'")
                profile[key] = matched
            continue

        if key == "mood_tag":
            profile[key] = str(value).strip().lower()
            continue

        try:
            number = float(value)
        except (TypeError, ValueError):
            fixes.append(f"dropped {key} '{value}' (not a number)")
            continue

        if key in UNIT_FEATURES:
            low, high = 0.0, 1.0
        elif key == "tempo_bpm":
            low, high = 40.0, 200.0
        elif key == "popularity":
            low, high = 0.0, 100.0
        else:  # release_decade
            number = round(number / 10) * 10
            low, high = 1950.0, 2020.0

        clamped = min(max(number, low), high)
        if clamped != number:
            fixes.append(f"clamped {key} {number:g} -> {clamped:g}")
        profile[key] = int(clamped) if key in ("popularity", "release_decade") else clamped

    if not any(k in profile for k in ("genre", "mood", "energy")):
        profile["energy"] = 0.5
        fixes.append("no genre, mood or energy left, so energy defaulted to 0.5")

    return profile, fixes


def extract_json(text: str) -> Optional[Dict]:
    """Pull the first JSON object out of an LLM reply (handles ```json fences)."""
    if not text:
        return None
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def verify_answer(raw_text: str, candidate_titles: List[str]) -> Tuple[bool, Optional[Dict], List[str]]:
    """
    Check the writer's answer. Returns (ok, cleaned answer, problems).
    The main job is catching made-up songs: every pick must be one of the candidates.
    """
    data = extract_json(raw_text)
    if data is None:
        return False, None, ["answer was not valid JSON"]

    problems: List[str] = []
    lookup = {t.lower(): t for t in candidate_titles}
    picks = data.get("picks")
    if not isinstance(picks, list):
        return False, None, ["answer has no 'picks' list"]

    cleaned, seen = [], set()
    for pick in picks:
        if not isinstance(pick, dict):
            problems.append("a pick was not an object")
            continue
        title = str(pick.get("title", "")).strip()
        reason = str(pick.get("reason", "")).strip()
        real = lookup.get(title.lower())
        if real is None:
            problems.append(f"'{title}' is not one of the retrieved songs")
        elif real in seen:
            problems.append(f"'{real}' was picked twice")
        elif not reason:
            problems.append(f"'{real}' has no reason")
        else:
            seen.add(real)
            cleaned.append({"title": real, "reason": reason})

    if not 3 <= len(picks) <= 5:
        problems.append(f"expected 3 to 5 picks, got {len(picks)}")
    summary = str(data.get("summary", "")).strip()
    if not summary:
        problems.append("summary is empty")

    ok = not problems
    return ok, {"summary": summary, "picks": cleaned}, problems
