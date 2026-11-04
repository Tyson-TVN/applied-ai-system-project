import csv
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple, Union


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_decade: int = 2020
    mood_tag: str = ""
    instrumentalness: float = 0.0
    speechiness: float = 0.0


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# Each mode is a set of point weights. A mode is the "ranking strategy": the scoring
# code never changes, only the weights it is handed.
SCORING_MODES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "genre": 2.0, "mood": 1.0, "mood_tag": 0.5, "energy": 1.0,
        "valence": 0.5, "danceability": 0.5, "acousticness": 0.5,
        "tempo_bpm": 0.5, "popularity": 0.5, "release_decade": 0.5,
    },
    "genre_first": {
        "genre": 4.0, "mood": 0.5, "mood_tag": 0.25, "energy": 0.5,
        "valence": 0.25, "danceability": 0.25, "acousticness": 0.25,
        "tempo_bpm": 0.25, "popularity": 0.25, "release_decade": 0.25,
    },
    "mood_first": {
        "genre": 0.5, "mood": 3.0, "mood_tag": 1.0, "energy": 0.5,
        "valence": 1.0, "danceability": 0.25, "acousticness": 0.25,
        "tempo_bpm": 0.25, "popularity": 0.25, "release_decade": 0.25,
    },
    "energy_focused": {
        "genre": 0.5, "mood": 0.5, "mood_tag": 0.25, "energy": 3.0,
        "valence": 0.25, "danceability": 0.5, "acousticness": 0.25,
        "tempo_bpm": 1.0, "popularity": 0.25, "release_decade": 0.25,
    },
}
DEFAULT_MODE = "balanced"

# Numeric features: (label for the explanation, how far apart counts as "totally different")
NUMERIC_FEATURES: Dict[str, Tuple[str, float]] = {
    "energy": ("energy", 1.0),
    "valence": ("valence", 1.0),
    "danceability": ("danceability", 1.0),
    "acousticness": ("acousticness", 1.0),
    "tempo_bpm": ("tempo", 100.0),
    "popularity": ("popularity", 100.0),
    "release_decade": ("decade", 50.0),
}

INT_COLUMNS = {"id", "popularity", "release_decade"}
FLOAT_COLUMNS = {
    "energy", "tempo_bpm", "valence", "danceability",
    "acousticness", "instrumentalness", "speechiness",
}


def load_songs(csv_path: str) -> List[Dict]:
    """Read the songs CSV into a list of dicts with numeric columns converted."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for col in INT_COLUMNS & row.keys():
                row[col] = int(row[col])
            for col in FLOAT_COLUMNS & row.keys():
                row[col] = float(row[col])
            songs.append(row)
    return songs


def _closeness(value: float, target: float, spread: float) -> float:
    """Return 1.0 for an exact match, falling to 0.0 once the gap reaches `spread`."""
    return max(0.0, 1.0 - abs(value - target) / spread)


def score_song(
    user_prefs: Dict,
    song: Dict,
    mode: Union[str, Dict[str, float]] = DEFAULT_MODE,
) -> Tuple[float, List[str]]:
    """Score one song against a taste profile and return (score, reasons)."""
    weights = SCORING_MODES[mode] if isinstance(mode, str) else mode
    score = 0.0
    reasons: List[str] = []

    if user_prefs.get("genre") == song.get("genre"):
        points = weights["genre"]
        score += points
        reasons.append(f"genre match: {song['genre']} (+{points:.2f})")

    if user_prefs.get("mood") == song.get("mood"):
        points = weights["mood"]
        score += points
        reasons.append(f"mood match: {song['mood']} (+{points:.2f})")

    wanted_tag = user_prefs.get("mood_tag")
    if wanted_tag and wanted_tag == song.get("mood_tag"):
        points = weights["mood_tag"]
        score += points
        reasons.append(f"mood tag match: {wanted_tag} (+{points:.2f})")

    # Numeric features only count when the profile actually states a target for them.
    for key, (label, spread) in NUMERIC_FEATURES.items():
        if key not in user_prefs or key not in song:
            continue
        points = weights[key] * _closeness(song[key], user_prefs[key], spread)
        if points >= 0.005:
            score += points
            reasons.append(
                f"{label} {song[key]:g} vs target {user_prefs[key]:g} (+{points:.2f})"
            )

    return round(score, 2), reasons


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: Union[str, Dict[str, float]] = DEFAULT_MODE,
    artist_penalty: float = 0.0,
    genre_penalty: float = 0.0,
) -> List[Tuple[Dict, float, str]]:
    """Score every song, rank them, and return the top k as (song, score, explanation)."""
    scored = [(song, *score_song(user_prefs, song, mode)) for song in songs]
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    if artist_penalty or genre_penalty:
        picks = _rerank_for_variety(ranked, k, artist_penalty, genre_penalty)
    else:
        picks = ranked[:k]

    return [(song, score, "; ".join(reasons)) for song, score, reasons in picks]


def _rerank_for_variety(
    ranked: List[Tuple[Dict, float, List[str]]],
    k: int,
    artist_penalty: float,
    genre_penalty: float,
) -> List[Tuple[Dict, float, List[str]]]:
    """Pick songs one at a time, docking points from artists and genres already chosen."""
    remaining = list(ranked)
    picks: List[Tuple[Dict, float, List[str]]] = []

    while remaining and len(picks) < k:
        best = None
        for index, (song, score, reasons) in enumerate(remaining):
            adjusted = score
            notes = []
            same_artist = sum(1 for p in picks if p[0]["artist"] == song["artist"])
            same_genre = sum(1 for p in picks if p[0]["genre"] == song["genre"])
            if same_artist and artist_penalty:
                cut = artist_penalty * same_artist
                adjusted -= cut
                notes.append(f"artist already in list (-{cut:.2f})")
            if same_genre and genre_penalty:
                cut = genre_penalty * same_genre
                adjusted -= cut
                notes.append(f"genre already in list (-{cut:.2f})")
            if best is None or adjusted > best[1]:
                best = (index, adjusted, notes)

        index, adjusted, notes = best
        song, _, reasons = remaining.pop(index)
        picks.append((song, round(adjusted, 2), reasons + notes))

    return picks


def profile_to_prefs(user: UserProfile) -> Dict:
    """Turn a UserProfile into the dict format the scoring function reads."""
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "acousticness": 0.8 if user.likes_acoustic else 0.2,
    }


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the k best songs for this user, highest score first."""
        prefs = profile_to_prefs(user)
        ranked = sorted(
            self.songs,
            key=lambda song: score_song(prefs, asdict(song))[0],
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Describe in words why this song scored the way it did for this user."""
        score, reasons = score_song(profile_to_prefs(user), asdict(song))
        if not reasons:
            return f"{song.title} scored {score:.2f}: nothing about it matched this profile."
        return f"{song.title} scored {score:.2f}: " + "; ".join(reasons)
