"""
Retrieval over the genre and activity guide (knowledge/genre_guide.md).

The guide is split into sections on "## " headings. A request is matched to
sections by keyword overlap. This is simple on purpose: it is easy to explain,
it runs offline, and with ~20 sections an embedding model would be overkill.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

GUIDE_PATH = "knowledge/genre_guide.md"

TOKEN_RE = re.compile(r"[a-z0-9&'-]+")


@dataclass
class Note:
    title: str
    keywords: Set[str]
    text: str
    hint: Dict[str, object] = field(default_factory=dict)


def tokenize(text: str) -> Set[str]:
    """Lowercase words, plus the word with a trailing 's' removed ("beats" -> "beat")."""
    words = set(TOKEN_RE.findall(text.lower()))
    return words | {w[:-1] for w in words if len(w) > 3 and w.endswith("s")}


def parse_hint(line: str) -> Dict[str, object]:
    """Turn 'genre=lofi; energy=0.40' into {'genre': 'lofi', 'energy': 0.4}."""
    hint: Dict[str, object] = {}
    for part in line.split(";"):
        if "=" not in part:
            continue
        key, value = (piece.strip() for piece in part.split("=", 1))
        try:
            hint[key] = float(value)
        except ValueError:
            hint[key] = value
    return hint


def load_guide(path: str = GUIDE_PATH) -> List[Note]:
    with open(path, encoding="utf-8") as f:
        content = f.read()

    notes = []
    for block in content.split("\n## ")[1:]:
        lines = block.strip().splitlines()
        title = lines[0].strip()
        keywords: Set[str] = set()
        hint: Dict[str, object] = {}
        body = []
        for line in lines[1:]:
            if line.startswith("Keywords:"):
                keywords = {k.strip().lower() for k in line[9:].split(",") if k.strip()}
            elif line.startswith("Profile hint:"):
                hint = parse_hint(line[13:])
            elif line.strip():
                body.append(line.strip())
        notes.append(Note(title, keywords, " ".join(body), hint))
    return notes


def score_note(request: str, note: Note) -> int:
    """Two points per matching keyword. Multi-word keywords must appear as a phrase."""
    text = request.lower()
    tokens = tokenize(request)
    score = 0
    for keyword in note.keywords:
        if " " in keyword:
            if keyword in text:
                score += 2
        elif keyword in tokens:
            score += 2
    return score


def retrieve(request: str, notes: List[Note], k: int = 3) -> List[Tuple[Note, int]]:
    """Return up to k notes that share at least one keyword with the request."""
    scored = [(note, score_note(request, note)) for note in notes]
    scored = [item for item in scored if item[1] > 0]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


def catalog_vocab(songs: List[Dict]) -> Tuple[Set[str], Set[str]]:
    """All genres and moods that actually exist in the song catalog."""
    return {s["genre"] for s in songs}, {s["mood"] for s in songs}
