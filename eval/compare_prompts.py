"""
Baseline vs specialized planner prompt.

Sends the same 8 requests to Gemini twice: once with the plain zero-shot prompt and
once with the few-shot prompt (catalog labels, rules and worked examples). No guide
notes are given to either, so the only difference is the prompt.

    python -m eval.compare_prompts

Saves the report to logs/prompt_comparison.txt. Needs GEMINI_API_KEY.
"""

import io
import time
from contextlib import redirect_stdout

from tabulate import tabulate

from src.guardrails import extract_json
from src.llm_client import get_client
from src.prompts import planner_prompt
from src.recommender import load_songs
from src.retriever import catalog_vocab

# (request, acceptable genres or None for "any", energy band)
REQUESTS = [
    ("quiet piano music for reading", {"classical"}, (0.0, 0.35)),
    ("songs to lift weights to", None, (0.8, 1.0)),
    ("rainy day blues", {"blues"}, (0.0, 0.5)),
    ("smooth music for a date night", {"r&b", "soul", "jazz"}, (0.3, 0.7)),
    ("lo-fi hip hop to code to", {"lofi"}, (0.0, 0.55)),
    ("rap bangers", {"hip-hop"}, (0.7, 1.0)),
    ("festival edm drops", {"edm"}, (0.8, 1.0)),
    ("country songs for a long drive", {"country"}, (0.3, 0.7)),
]


def evaluate(profile, genres, expected_genres, band):
    """Return (valid json, genre is a real catalog label, expected genre hit, energy in band)."""
    if profile is None:
        return False, False, False, False
    genre = str(profile.get("genre", "")).strip().lower()
    in_catalog = genre in genres if genre else expected_genres is None
    hit = (genre in expected_genres) if expected_genres else in_catalog
    try:
        energy_ok = band[0] <= float(profile.get("energy")) <= band[1]
    except (TypeError, ValueError):
        energy_ok = False
    return True, in_catalog, hit, energy_ok


def main(delay: float = 4.0) -> None:
    client = get_client()
    if client is None:
        print("This comparison needs GEMINI_API_KEY in .env.")
        return
    genres, moods = catalog_vocab(load_songs("data/songs.csv"))
    totals = {"zero_shot": [0, 0, 0, 0], "few_shot": [0, 0, 0, 0]}
    rows = []

    for request, expected, band in REQUESTS:
        row = [request]
        for style in ("zero_shot", "few_shot"):
            reply = client.complete(planner_prompt(style, genres, moods), f'Request: "{request}"')
            profile = extract_json(reply)
            checks = evaluate(profile, genres, expected, band)
            totals[style] = [t + c for t, c in zip(totals[style], checks)]
            if profile is None:
                row.append("invalid JSON")
            else:
                row.append(f"{profile.get('genre', '-')} / {profile.get('mood', '-')} / {profile.get('energy', '-')}")
            time.sleep(delay)
        rows.append(row)

    n = len(REQUESTS)
    out = io.StringIO()
    with redirect_stdout(out):
        print(f"Planner prompt comparison - model: {client.model_name}\n")
        print(tabulate(rows, headers=["Request", "Zero-shot (genre / mood / energy)",
                                      "Few-shot (genre / mood / energy)"], tablefmt="github"))
        print()
        labels = ["Valid JSON", "Genre is a real catalog label", "Expected genre hit", "Energy in expected band"]
        summary = [[label, f"{totals['zero_shot'][i]}/{n}", f"{totals['few_shot'][i]}/{n}"]
                   for i, label in enumerate(labels)]
        print(tabulate(summary, headers=["Metric", "Zero-shot", "Few-shot"], tablefmt="github"))
    report = out.getvalue()
    print(report)
    with open("logs/prompt_comparison.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("Saved to logs/prompt_comparison.txt")


if __name__ == "__main__":
    main()
