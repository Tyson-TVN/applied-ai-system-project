"""
Command line runner for the Music Recommender Simulation.

Run it from the project root:
    python -m src.main
    python -m src.main --mode genre_first
"""

import argparse

from tabulate import tabulate

from src.recommender import SCORING_MODES, load_songs, recommend_songs


PROFILES = {
    "Default Pop/Happy": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9, "valence": 0.9},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.38, "acousticness": 0.8},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.92, "tempo_bpm": 150},
    "Nostalgic Throwback": {
        "genre": "soul", "mood": "happy", "energy": 0.6,
        "mood_tag": "nostalgic", "release_decade": 1970, "popularity": 70,
    },
}

# Profiles built to confuse the scoring rule.
EDGE_CASES = {
    "Conflicted (sad but high energy)": {"genre": "blues", "mood": "sad", "energy": 0.9},
    "Genre Not In Catalog (k-pop)": {"genre": "k-pop", "mood": "happy", "energy": 0.7},
    "Mood Only (no genre fan)": {"mood": "peaceful", "energy": 0.2},
}

# Weight experiment: genre counts half as much, energy twice as much.
EXPERIMENT_WEIGHTS = {**SCORING_MODES["balanced"], "genre": 1.0, "energy": 2.0}


def show_table(recommendations) -> None:
    """Print ranked recommendations as a table with the reasons behind each score."""
    rows = [
        [rank, song["title"], song["artist"], song["genre"], f"{score:.2f}", explanation]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]
    headers = ["#", "Title", "Artist", "Genre", "Score", "Why"]
    print(tabulate(rows, headers=headers, tablefmt="grid", disable_numparse=True,
                   maxcolwidths=[None, 22, 16, 10, None, 62]))
    print()


def show_profile(name, prefs, songs, k=5, **options) -> None:
    """Print a profile heading followed by its top k recommendations."""
    print(f"=== {name} ===")
    print(f"Profile: {prefs}")
    show_table(recommend_songs(prefs, songs, k=k, **options))


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("--mode", choices=sorted(SCORING_MODES), default="balanced",
                        help="which ranking strategy to use for the profile runs")
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"Ranking mode: {args.mode}\n")

    print("##### USER PROFILES #####\n")
    for name, prefs in PROFILES.items():
        show_profile(name, prefs, songs, mode=args.mode)

    print("##### EDGE-CASE PROFILES #####\n")
    for name, prefs in EDGE_CASES.items():
        show_profile(name, prefs, songs, mode=args.mode)

    print("##### RANKING MODES (Default Pop/Happy, top 3) #####\n")
    for mode in SCORING_MODES:
        show_profile(f"mode: {mode}", PROFILES["Default Pop/Happy"], songs, k=3, mode=mode)

    print("##### WEIGHT EXPERIMENT (Default Pop/Happy, top 5) #####\n")
    show_profile("genre weight 1.0, energy weight 2.0", PROFILES["Default Pop/Happy"],
                 songs, mode=EXPERIMENT_WEIGHTS)

    print("##### DIVERSITY PENALTY (Chill Lofi, top 5) #####\n")
    show_profile("no penalty", PROFILES["Chill Lofi"], songs)
    show_profile("artist penalty 0.5, genre penalty 0.5", PROFILES["Chill Lofi"], songs,
                 artist_penalty=0.5, genre_penalty=0.5)


if __name__ == "__main__":
    main()
