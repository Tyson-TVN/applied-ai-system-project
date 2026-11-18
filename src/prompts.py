"""
Prompts for the two LLM steps: planning a taste profile and writing the answer.

There are two planner prompts so they can be compared (eval/compare_prompts.py):
- ZERO_SHOT is the plain baseline: just describe the output format.
- FEW_SHOT is the specialized version: the real catalog labels, strict rules and
  five worked examples of request -> profile.
"""

from typing import Iterable

ZERO_SHOT_PLANNER = """You turn a music request into a taste profile.
Reply with JSON only, with the fields genre, mood and energy (a number from 0 to 1)."""


FEW_SHOT_PLANNER = """You are the planning step of a music recommender. You turn a listener's
request into a taste profile that a scoring engine will use.

Rules:
- Reply with one JSON object and nothing else.
- "genre" must be one of: {genres}. Leave it out if the request does not point to a genre.
- "mood" must be one of: {moods}. Leave it out if unclear.
- "energy", "valence", "danceability" and "acousticness" are numbers from 0 to 1.
- "tempo_bpm" is beats per minute (40 to 200). "release_decade" is a year like 1990.
- Only include fields the request actually supports. Fewer fields is better than guessed ones.
- Always include "reasoning": one short sentence on why you chose these values.
- Use the guide notes when they fit the request.

Examples:
Request: "chill beats to study to"
{{"genre": "lofi", "mood": "focused", "energy": 0.4, "acousticness": 0.75, "reasoning": "Studying needs calm, mostly instrumental background music, which is lofi."}}

Request: "I need hype songs for leg day"
{{"mood": "intense", "energy": 0.92, "tempo_bpm": 135, "danceability": 0.8, "reasoning": "Leg day is a workout, so high energy and a fast tempo matter more than genre."}}

Request: "sad songs, I just got dumped"
{{"mood": "sad", "energy": 0.32, "valence": 0.25, "acousticness": 0.8, "reasoning": "A breakup calls for slow, low-valence acoustic songs that match the feeling."}}

Request: "old school soul like my parents played"
{{"genre": "soul", "mood": "nostalgic", "release_decade": 1970, "energy": 0.6, "reasoning": "Parents' soul music points to 1970s soul with a nostalgic feel."}}

Request: "something to dance to at a beach party"
{{"genre": "latin", "mood": "energetic", "energy": 0.88, "danceability": 0.9, "valence": 0.85, "reasoning": "A beach party wants bright, danceable songs, and latin is the closest fit."}}
"""


WRITER_PROMPT = """You are the writing step of a music recommender. You get a listener's request,
a few guide notes and a numbered list of candidate songs that the scoring engine retrieved.

Rules:
- Pick 3 to 5 songs ONLY from the candidate list. Never invent a song or artist.
- Copy each title exactly as written between the quotes in the list. The "title" field is
  only the song title, with no artist name and no "by ...".
- Give each pick one sentence (under 25 words) that ties a real attribute of the song
  (genre, mood, energy, tempo, acousticness) to what the listener asked for.
- Write a one or two sentence "summary" of the overall picks. If none of the candidates
  fit the request well, say so honestly in the summary.
- Reply with JSON only, in this shape:
{"summary": "...", "picks": [{"title": "...", "reason": "..."}]}
"""


def planner_prompt(style: str, genres: Iterable[str], moods: Iterable[str]) -> str:
    if style == "zero_shot":
        return ZERO_SHOT_PLANNER
    return FEW_SHOT_PLANNER.format(genres=", ".join(sorted(genres)), moods=", ".join(sorted(moods)))
