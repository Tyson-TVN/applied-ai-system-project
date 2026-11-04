# 🎵 Music Recommender Simulation

## Project Summary

This project is a small music recommender that runs in the terminal. It reads a catalog of 25 songs from a CSV file, compares each song to a "taste profile" (favorite genre, favorite mood, target energy, and a few optional extras), gives every song a score, and prints the top matches along with the reasons for each score.

It is a content-based recommender. It only looks at what the songs are like (genre, mood, energy, tempo and so on). It does not look at what other listeners did. Every recommendation comes with a plain-text reason, so you can see exactly where the points came from.

Extra things I added on top of the basics:

- Five new song columns: popularity, release decade, a detailed mood tag, instrumentalness and speechiness.
- Four ranking modes (`balanced`, `genre_first`, `mood_first`, `energy_focused`) that you can switch between from the command line.
- A diversity penalty that lowers the score of a song when its artist or genre is already in the list.
- A formatted table for the output, with the reasons shown next to each score.

---

## How The System Works

### How real recommenders work

Apps like Spotify and YouTube work with two big families of ideas.

- **Collaborative filtering** uses other people's behavior. If listeners who liked the same songs as you also liked a new song, that song gets suggested to you. It needs no knowledge of the music itself, just lots of listening history: plays, skips, replays, likes, playlist adds, and how long someone stayed on a track.
- **Content-based filtering** uses the songs' own attributes: genre, mood, tempo, energy, how acoustic it is, the artist, the release year. If you like fast, high-energy songs, it looks for more songs with those traits.

Real apps blend both, and they usually work in two stages: first narrow millions of songs down to a few hundred candidates, then score and rank those candidates. My project does the same thing in miniature, but only the content-based half, and with a catalog small enough to score every song.

### Input data, user preferences, and ranking

- **Input data:** the song catalog (`data/songs.csv`). Each row is one song and its attributes.
- **User preferences:** a taste profile, which is a dictionary of targets such as `{"genre": "pop", "mood": "happy", "energy": 0.8}`.
- **Ranking:** a *scoring rule* judges one song against the profile and returns a number. A *ranking rule* applies the scoring rule to every song, sorts from highest to lowest, and keeps the top k. We need both because a single score means nothing until it is compared with the other songs' scores.

### Features used

**Each `Song` has:** id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness, popularity, release_decade, mood_tag, instrumentalness, speechiness.

**A taste profile can have:** `genre`, `mood`, `mood_tag`, `energy`, `valence`, `danceability`, `acousticness`, `tempo_bpm`, `popularity`, `release_decade`. Only `genre`, `mood` and `energy` are needed. Any feature that is left out of the profile is simply not scored. (The `UserProfile` class used by the tests stores favorite genre, favorite mood, target energy and whether the user likes acoustic songs.)

### Algorithm recipe (balanced mode)

| Rule | Points |
|---|---|
| Genre matches exactly | +2.0 |
| Mood matches exactly | +1.0 |
| Mood tag matches exactly | +0.5 |
| Energy closeness | up to +1.0 |
| Valence, danceability, acousticness, tempo, popularity, decade closeness | up to +0.5 each |

For numbers, the points are `weight × (1 − gap / spread)`, never below zero. A song with exactly the target energy gets the full weight. A song that is far away gets close to nothing. This rewards being *close* to the target, not just being high or low. The spread is 1.0 for the 0-to-1 features, 100 for tempo and popularity, and 50 for decade.

The other modes keep the same rules but change the weights. `genre_first` makes genre worth 4.0, `mood_first` makes mood worth 3.0, and `energy_focused` makes energy worth 3.0.

### Data flow

```
INPUT    taste profile (dict)  +  data/songs.csv
           |
PROCESS    for every song: score_song(profile, song) -> (score, reasons)
           |
OUTPUT     sort by score, highest first -> top k songs with their reasons
```

### Biases I expected before testing

- Genre is worth the most points, so the system probably over-prioritizes genre and can bury a great song that matches the mood and energy perfectly but sits in a different genre.
- Genre and mood are exact text matches. "indie pop" gets nothing for a "pop" fan, and "relaxed" gets nothing for a "chill" fan, even though a person would call those close.
- Most genres have only one song, so a genre fan runs out of real matches quickly.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app from the project folder:

   ```bash
   python -m src.main
   ```

   To change the ranking mode used for the profile runs:

   ```bash
   python -m src.main --mode genre_first
   ```

   The choices are `balanced` (default), `genre_first`, `mood_first` and `energy_focused`.

### Running Tests

```bash
pytest
```

---

## Sample Recommendation Output

This is the default "pop / happy" profile, run in balanced mode:

```
=== Default Pop/Happy ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| #   | Title              | Artist        | Genre     | Score   | Why                                                          |
+=====+====================+===============+===========+=========+==============================================================+
| 1   | Sunrise City       | Neon Echo     | pop       | 3.98    | genre match: pop (+2.00); mood match: happy (+1.00); energy  |
|     |                    |               |           |         | 0.82 vs target 0.8 (+0.98)                                   |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 2   | Neon Confetti      | Candy Static  | pop       | 3.92    | genre match: pop (+2.00); mood match: happy (+1.00); energy  |
|     |                    |               |           |         | 0.88 vs target 0.8 (+0.92)                                   |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 3   | Gym Hero           | Max Pulse     | pop       | 2.87    | genre match: pop (+2.00); energy 0.93 vs target 0.8 (+0.87)  |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 4   | Rooftop Lights     | Indigo Parade | indie pop | 1.96    | mood match: happy (+1.00); energy 0.76 vs target 0.8 (+0.96) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 5   | Golden Hour Groove | Velour Kings  | soul      | 1.82    | mood match: happy (+1.00); energy 0.62 vs target 0.8 (+0.82) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
```

Sunrise City and Neon Confetti come first because they match on genre, mood and energy. Gym Hero is third even though its mood is "intense" and not "happy". It matches on genre (+2.0) and its energy is close, and that is already more than Rooftop Lights gets for a mood match plus good energy.

---

## Experiments You Tried

### Different user profiles

Each profile was run with the balanced mode. The top 5 for each are below, and the model card (`model_card.md`) has the comparisons between them.

**High-Energy Pop**

```
=== High-Energy Pop ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.9, 'valence': 0.9}
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| #   | Title              | Artist        | Genre     | Score   | Why                                                            |
+=====+====================+===============+===========+=========+================================================================+
| 1   | Neon Confetti      | Candy Static  | pop       | 4.47    | genre match: pop (+2.00); mood match: happy (+1.00); energy    |
|     |                    |               |           |         | 0.88 vs target 0.9 (+0.98); valence 0.92 vs target 0.9 (+0.49) |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 2   | Sunrise City       | Neon Echo     | pop       | 4.39    | genre match: pop (+2.00); mood match: happy (+1.00); energy    |
|     |                    |               |           |         | 0.82 vs target 0.9 (+0.92); valence 0.84 vs target 0.9 (+0.47) |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 3   | Gym Hero           | Max Pulse     | pop       | 3.40    | genre match: pop (+2.00); energy 0.93 vs target 0.9 (+0.97);   |
|     |                    |               |           |         | valence 0.77 vs target 0.9 (+0.43)                             |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 4   | Rooftop Lights     | Indigo Parade | indie pop | 2.31    | mood match: happy (+1.00); energy 0.76 vs target 0.9 (+0.86);  |
|     |                    |               |           |         | valence 0.81 vs target 0.9 (+0.46)                             |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 5   | Golden Hour Groove | Velour Kings  | soul      | 2.21    | mood match: happy (+1.00); energy 0.62 vs target 0.9 (+0.72);  |
|     |                    |               |           |         | valence 0.88 vs target 0.9 (+0.49)                             |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
```

**Chill Lofi**

```
=== Chill Lofi ===
Profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.38, 'acousticness': 0.8}
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| #   | Title               | Artist         | Genre   | Score   | Why                                                            |
+=====+=====================+================+=========+=========+================================================================+
| 1   | Library Rain        | Paper Lanterns | lofi    | 4.44    | genre match: lofi (+2.00); mood match: chill (+1.00); energy   |
|     |                     |                |         |         | 0.35 vs target 0.38 (+0.97); acousticness 0.86 vs target 0.8   |
|     |                     |                |         |         | (+0.47)                                                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | lofi    | 4.42    | genre match: lofi (+2.00); mood match: chill (+1.00); energy   |
|     |                     |                |         |         | 0.42 vs target 0.38 (+0.96); acousticness 0.71 vs target 0.8   |
|     |                     |                |         |         | (+0.45)                                                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 3   | Focus Flow          | LoRoom         | lofi    | 3.47    | genre match: lofi (+2.00); energy 0.4 vs target 0.38 (+0.98);  |
|     |                     |                |         |         | acousticness 0.78 vs target 0.8 (+0.49)                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 4   | Spacewalk Thoughts  | Orbit Bloom    | ambient | 2.34    | mood match: chill (+1.00); energy 0.28 vs target 0.38 (+0.90); |
|     |                     |                |         |         | acousticness 0.92 vs target 0.8 (+0.44)                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 5   | Rainy Highway Blues | Delta Mae      | blues   | 1.46    | energy 0.4 vs target 0.38 (+0.98); acousticness 0.75 vs target |
|     |                     |                |         |         | 0.8 (+0.47)                                                    |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
```

**Deep Intense Rock**

```
=== Deep Intense Rock ===
Profile: {'genre': 'rock', 'mood': 'intense', 'energy': 0.92, 'tempo_bpm': 150}
+-----+----------------+--------------+---------+---------+----------------------------------------------------------------+
| #   | Title          | Artist       | Genre   | Score   | Why                                                            |
+=====+================+==============+=========+=========+================================================================+
| 1   | Storm Runner   | Voltline     | rock    | 4.48    | genre match: rock (+2.00); mood match: intense (+1.00); energy |
|     |                |              |         |         | 0.91 vs target 0.92 (+0.99); tempo 152 vs target 150 (+0.49)   |
+-----+----------------+--------------+---------+---------+----------------------------------------------------------------+
| 2   | Gym Hero       | Max Pulse    | pop     | 2.40    | mood match: intense (+1.00); energy 0.93 vs target 0.92        |
|     |                |              |         |         | (+0.99); tempo 132 vs target 150 (+0.41)                       |
+-----+----------------+--------------+---------+---------+----------------------------------------------------------------+
| 3   | Concrete Crown | Rhyme Atlas  | hip-hop | 2.15    | mood match: intense (+1.00); energy 0.84 vs target 0.92        |
|     |                |              |         |         | (+0.92); tempo 96 vs target 150 (+0.23)                        |
+-----+----------------+--------------+---------+---------+----------------------------------------------------------------+
| 4   | Iron Requiem   | Black Anvil  | metal   | 1.36    | energy 0.97 vs target 0.92 (+0.95); tempo 168 vs target 150    |
|     |                |              |         |         | (+0.41)                                                        |
+-----+----------------+--------------+---------+---------+----------------------------------------------------------------+
| 5   | Bass Cathedral | Pulse Theory | edm     | 1.35    | energy 0.96 vs target 0.92 (+0.96); tempo 128 vs target 150    |
|     |                |              |         |         | (+0.39)                                                        |
+-----+----------------+--------------+---------+---------+----------------------------------------------------------------+
```

**Nostalgic Throwback** (uses the extra columns: mood tag, decade, popularity)

```
=== Nostalgic Throwback ===
Profile: {'genre': 'soul', 'mood': 'happy', 'energy': 0.6, 'mood_tag': 'nostalgic', 'release_decade': 1970, 'popularity': 70}
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| #   | Title              | Artist        | Genre     | Score   | Why                                                            |
+=====+====================+===============+===========+=========+================================================================+
| 1   | Golden Hour Groove | Velour Kings  | soul      | 5.47    | genre match: soul (+2.00); mood match: happy (+1.00); mood tag |
|     |                    |               |           |         | match: nostalgic (+0.50); energy 0.62 vs target 0.6 (+0.98);   |
|     |                    |               |           |         | popularity 72 vs target 70 (+0.49); decade 1970 vs target 1970 |
|     |                    |               |           |         | (+0.50)                                                        |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 2   | Rooftop Lights     | Indigo Parade | indie pop | 2.44    | mood match: happy (+1.00); energy 0.76 vs target 0.6 (+0.84);  |
|     |                    |               |           |         | popularity 69 vs target 70 (+0.49); decade 2010 vs target 1970 |
|     |                    |               |           |         | (+0.10)                                                        |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 3   | Sunrise City       | Neon Echo     | pop       | 2.22    | mood match: happy (+1.00); energy 0.82 vs target 0.6 (+0.78);  |
|     |                    |               |           |         | popularity 82 vs target 70 (+0.44)                             |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 4   | Neon Confetti      | Candy Static  | pop       | 2.12    | mood match: happy (+1.00); energy 0.88 vs target 0.6 (+0.72);  |
|     |                    |               |           |         | popularity 90 vs target 70 (+0.40)                             |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
| 5   | Dusty Porch Song   | Hollow Pines  | country   | 2.00    | mood tag match: nostalgic (+0.50); energy 0.45 vs target 0.6   |
|     |                    |               |           |         | (+0.85); popularity 60 vs target 70 (+0.45); decade 2000 vs    |
|     |                    |               |           |         | target 1970 (+0.20)                                            |
+-----+--------------------+---------------+-----------+---------+----------------------------------------------------------------+
```

### Edge-case profiles

These were built to confuse the scoring rule.

**Conflicted: sad mood but very high energy**

```
=== Conflicted (sad but high energy) ===
Profile: {'genre': 'blues', 'mood': 'sad', 'energy': 0.9}
+-----+---------------------+-----------------+---------+---------+-------------------------------------------------------------+
| #   | Title               | Artist          | Genre   | Score   | Why                                                         |
+=====+=====================+=================+=========+=========+=============================================================+
| 1   | Rainy Highway Blues | Delta Mae       | blues   | 3.50    | genre match: blues (+2.00); mood match: sad (+1.00); energy |
|     |                     |                 |         |         | 0.4 vs target 0.9 (+0.50)                                   |
+-----+---------------------+-----------------+---------+---------+-------------------------------------------------------------+
| 2   | Last Train Home     | Hollow Pines    | country | 1.58    | mood match: sad (+1.00); energy 0.48 vs target 0.9 (+0.58)  |
+-----+---------------------+-----------------+---------+---------+-------------------------------------------------------------+
| 3   | Paper Boats         | Willow and Pine | folk    | 1.40    | mood match: sad (+1.00); energy 0.3 vs target 0.9 (+0.40)   |
+-----+---------------------+-----------------+---------+---------+-------------------------------------------------------------+
| 4   | Storm Runner        | Voltline        | rock    | 0.99    | energy 0.91 vs target 0.9 (+0.99)                           |
+-----+---------------------+-----------------+---------+---------+-------------------------------------------------------------+
| 5   | Fuego Nocturno      | Luz Calle       | latin   | 0.98    | energy 0.88 vs target 0.9 (+0.98)                           |
+-----+---------------------+-----------------+---------+---------+-------------------------------------------------------------+
```

**A genre that is not in the catalog**

```
=== Genre Not In Catalog (k-pop) ===
Profile: {'genre': 'k-pop', 'mood': 'happy', 'energy': 0.7}
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| #   | Title              | Artist        | Genre     | Score   | Why                                                          |
+=====+====================+===============+===========+=========+==============================================================+
| 1   | Rooftop Lights     | Indigo Parade | indie pop | 1.94    | mood match: happy (+1.00); energy 0.76 vs target 0.7 (+0.94) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 2   | Golden Hour Groove | Velour Kings  | soul      | 1.92    | mood match: happy (+1.00); energy 0.62 vs target 0.7 (+0.92) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 3   | Sunrise City       | Neon Echo     | pop       | 1.88    | mood match: happy (+1.00); energy 0.82 vs target 0.7 (+0.88) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 4   | Neon Confetti      | Candy Static  | pop       | 1.82    | mood match: happy (+1.00); energy 0.88 vs target 0.7 (+0.82) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 5   | Night Drive Loop   | Neon Echo     | synthwave | 0.95    | energy 0.75 vs target 0.7 (+0.95)                            |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
```

**Mood only, no favorite genre**

```
=== Mood Only (no genre fan) ===
Profile: {'mood': 'peaceful', 'energy': 0.2}
+-----+--------------------+-----------------+-----------+---------+---------------------------------------------------------+
| #   | Title              | Artist          | Genre     | Score   | Why                                                     |
+=====+====================+=================+===========+=========+=========================================================+
| 1   | Nocturne in Blue   | Elena Marsh     | classical | 1.98    | mood match: peaceful (+1.00); energy 0.18 vs target 0.2 |
|     |                    |                 |           |         | (+0.98)                                                 |
+-----+--------------------+-----------------+-----------+---------+---------------------------------------------------------+
| 2   | Glass Garden       | Orbit Bloom     | ambient   | 1.98    | mood match: peaceful (+1.00); energy 0.22 vs target 0.2 |
|     |                    |                 |           |         | (+0.98)                                                 |
+-----+--------------------+-----------------+-----------+---------+---------------------------------------------------------+
| 3   | Spacewalk Thoughts | Orbit Bloom     | ambient   | 0.92    | energy 0.28 vs target 0.2 (+0.92)                       |
+-----+--------------------+-----------------+-----------+---------+---------------------------------------------------------+
| 4   | Paper Boats        | Willow and Pine | folk      | 0.90    | energy 0.3 vs target 0.2 (+0.90)                        |
+-----+--------------------+-----------------+-----------+---------+---------------------------------------------------------+
| 5   | Library Rain       | Paper Lanterns  | lofi      | 0.85    | energy 0.35 vs target 0.2 (+0.85)                       |
+-----+--------------------+-----------------+-----------+---------+---------------------------------------------------------+
```

### Ranking modes (default pop / happy, top 3)

```

=== mode: balanced ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+
| #   | Title         | Artist       | Genre   | Score   | Why                                                         |
+=====+===============+==============+=========+=========+=============================================================+
| 1   | Sunrise City  | Neon Echo    | pop     | 3.98    | genre match: pop (+2.00); mood match: happy (+1.00); energy |
|     |               |              |         |         | 0.82 vs target 0.8 (+0.98)                                  |
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+
| 2   | Neon Confetti | Candy Static | pop     | 3.92    | genre match: pop (+2.00); mood match: happy (+1.00); energy |
|     |               |              |         |         | 0.88 vs target 0.8 (+0.92)                                  |
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+
| 3   | Gym Hero      | Max Pulse    | pop     | 2.87    | genre match: pop (+2.00); energy 0.93 vs target 0.8 (+0.87) |
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+

=== mode: genre_first ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+
| #   | Title         | Artist       | Genre   | Score   | Why                                                         |
+=====+===============+==============+=========+=========+=============================================================+
| 1   | Sunrise City  | Neon Echo    | pop     | 4.99    | genre match: pop (+4.00); mood match: happy (+0.50); energy |
|     |               |              |         |         | 0.82 vs target 0.8 (+0.49)                                  |
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+
| 2   | Neon Confetti | Candy Static | pop     | 4.96    | genre match: pop (+4.00); mood match: happy (+0.50); energy |
|     |               |              |         |         | 0.88 vs target 0.8 (+0.46)                                  |
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+
| 3   | Gym Hero      | Max Pulse    | pop     | 4.43    | genre match: pop (+4.00); energy 0.93 vs target 0.8 (+0.43) |
+-----+---------------+--------------+---------+---------+-------------------------------------------------------------+

=== mode: mood_first ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
| #   | Title          | Artist        | Genre     | Score   | Why                                                          |
+=====+================+===============+===========+=========+==============================================================+
| 1   | Sunrise City   | Neon Echo     | pop       | 3.99    | genre match: pop (+0.50); mood match: happy (+3.00); energy  |
|     |                |               |           |         | 0.82 vs target 0.8 (+0.49)                                   |
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
| 2   | Neon Confetti  | Candy Static  | pop       | 3.96    | genre match: pop (+0.50); mood match: happy (+3.00); energy  |
|     |                |               |           |         | 0.88 vs target 0.8 (+0.46)                                   |
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
| 3   | Rooftop Lights | Indigo Parade | indie pop | 3.48    | mood match: happy (+3.00); energy 0.76 vs target 0.8 (+0.48) |
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+

=== mode: energy_focused ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
| #   | Title          | Artist        | Genre     | Score   | Why                                                          |
+=====+================+===============+===========+=========+==============================================================+
| 1   | Sunrise City   | Neon Echo     | pop       | 3.94    | genre match: pop (+0.50); mood match: happy (+0.50); energy  |
|     |                |               |           |         | 0.82 vs target 0.8 (+2.94)                                   |
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
| 2   | Neon Confetti  | Candy Static  | pop       | 3.76    | genre match: pop (+0.50); mood match: happy (+0.50); energy  |
|     |                |               |           |         | 0.88 vs target 0.8 (+2.76)                                   |
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
| 3   | Rooftop Lights | Indigo Parade | indie pop | 3.38    | mood match: happy (+0.50); energy 0.76 vs target 0.8 (+2.88) |
+-----+----------------+---------------+-----------+---------+--------------------------------------------------------------+
```

Genre-first keeps Gym Hero in third place with a big score. Mood-first and energy-focused both push Gym Hero out and let Rooftop Lights (a happy song, but indie pop) take third.

### Weight shift experiment

I halved the genre weight (2.0 to 1.0) and doubled the energy weight (1.0 to 2.0):

```
=== genre weight 1.0, energy weight 2.0 ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| #   | Title              | Artist        | Genre     | Score   | Why                                                          |
+=====+====================+===============+===========+=========+==============================================================+
| 1   | Sunrise City       | Neon Echo     | pop       | 3.96    | genre match: pop (+1.00); mood match: happy (+1.00); energy  |
|     |                    |               |           |         | 0.82 vs target 0.8 (+1.96)                                   |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 2   | Neon Confetti      | Candy Static  | pop       | 3.84    | genre match: pop (+1.00); mood match: happy (+1.00); energy  |
|     |                    |               |           |         | 0.88 vs target 0.8 (+1.84)                                   |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 3   | Rooftop Lights     | Indigo Parade | indie pop | 2.92    | mood match: happy (+1.00); energy 0.76 vs target 0.8 (+1.92) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 4   | Gym Hero           | Max Pulse     | pop       | 2.74    | genre match: pop (+1.00); energy 0.93 vs target 0.8 (+1.74)  |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
| 5   | Golden Hour Groove | Velour Kings  | soul      | 2.64    | mood match: happy (+1.00); energy 0.62 vs target 0.8 (+1.64) |
+-----+--------------------+---------------+-----------+---------+--------------------------------------------------------------+
```

The top two stayed the same, but Gym Hero dropped from third to fourth behind Rooftop Lights. The change made the list more *accurate* for a "happy" listener, not just different, because Rooftop Lights is actually a happy song and Gym Hero is a workout track. The math is still valid: every score is a sum of parts that are never negative, so a better match can only add points.

### Diversity penalty (Chill Lofi)

```
=== no penalty ===
Profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.38, 'acousticness': 0.8}
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| #   | Title               | Artist         | Genre   | Score   | Why                                                            |
+=====+=====================+================+=========+=========+================================================================+
| 1   | Library Rain        | Paper Lanterns | lofi    | 4.44    | genre match: lofi (+2.00); mood match: chill (+1.00); energy   |
|     |                     |                |         |         | 0.35 vs target 0.38 (+0.97); acousticness 0.86 vs target 0.8   |
|     |                     |                |         |         | (+0.47)                                                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | lofi    | 4.42    | genre match: lofi (+2.00); mood match: chill (+1.00); energy   |
|     |                     |                |         |         | 0.42 vs target 0.38 (+0.96); acousticness 0.71 vs target 0.8   |
|     |                     |                |         |         | (+0.45)                                                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 3   | Focus Flow          | LoRoom         | lofi    | 3.47    | genre match: lofi (+2.00); energy 0.4 vs target 0.38 (+0.98);  |
|     |                     |                |         |         | acousticness 0.78 vs target 0.8 (+0.49)                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 4   | Spacewalk Thoughts  | Orbit Bloom    | ambient | 2.34    | mood match: chill (+1.00); energy 0.28 vs target 0.38 (+0.90); |
|     |                     |                |         |         | acousticness 0.92 vs target 0.8 (+0.44)                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 5   | Rainy Highway Blues | Delta Mae      | blues   | 1.46    | energy 0.4 vs target 0.38 (+0.98); acousticness 0.75 vs target |
|     |                     |                |         |         | 0.8 (+0.47)                                                    |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
=== artist penalty 0.5, genre penalty 0.5 ===
Profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.38, 'acousticness': 0.8}
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| #   | Title               | Artist         | Genre   | Score   | Why                                                            |
+=====+=====================+================+=========+=========+================================================================+
| 1   | Library Rain        | Paper Lanterns | lofi    | 4.44    | genre match: lofi (+2.00); mood match: chill (+1.00); energy   |
|     |                     |                |         |         | 0.35 vs target 0.38 (+0.97); acousticness 0.86 vs target 0.8   |
|     |                     |                |         |         | (+0.47)                                                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | lofi    | 3.92    | genre match: lofi (+2.00); mood match: chill (+1.00); energy   |
|     |                     |                |         |         | 0.42 vs target 0.38 (+0.96); acousticness 0.71 vs target 0.8   |
|     |                     |                |         |         | (+0.45); genre already in list (-0.50)                         |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 3   | Spacewalk Thoughts  | Orbit Bloom    | ambient | 2.34    | mood match: chill (+1.00); energy 0.28 vs target 0.38 (+0.90); |
|     |                     |                |         |         | acousticness 0.92 vs target 0.8 (+0.44)                        |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 4   | Focus Flow          | LoRoom         | lofi    | 1.97    | genre match: lofi (+2.00); energy 0.4 vs target 0.38 (+0.98);  |
|     |                     |                |         |         | acousticness 0.78 vs target 0.8 (+0.49); artist already in     |
|     |                     |                |         |         | list (-0.50); genre already in list (-1.00)                    |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
| 5   | Rainy Highway Blues | Delta Mae      | blues   | 1.46    | energy 0.4 vs target 0.38 (+0.98); acousticness 0.75 vs target |
|     |                     |                |         |         | 0.8 (+0.47)                                                    |
+-----+---------------------+----------------+---------+---------+----------------------------------------------------------------+
```

Without the penalty, LoRoom appears twice and lofi takes three of the top five spots. With it, the second LoRoom song loses points for repeating the artist and the genre, so Spacewalk Thoughts moves up ahead of Focus Flow. The penalty is shown in the reasons column.

---

## Limitations and Risks

- It only works on a catalog of 25 invented songs. 15 of the 19 genres have exactly one song.
- Genre and mood are exact text matches, so near-neighbors like "pop" and "indie pop" count as totally different.
- It cannot notice a conflicting profile. A blues fan who wants sad songs at energy 0.9 still gets slow blues first, because the genre and mood points are bigger than anything energy can earn.
- It does not understand lyrics, language, artists, or anything about the listener's history.
- Genre is the heaviest rule, so users who name a genre will keep getting that genre.

More detail is in the [model card](model_card.md).

---

## Reflection

The biggest thing I learned is that a recommender is mostly a set of choices about weights. I never wrote a rule that says "show Gym Hero to happy pop fans," but giving genre 2 points and mood only 1 point made it happen anyway. Changing a single number moved songs around the whole list, so the weights are where the taste of the system lives. The reasons column helped a lot too. Whenever a result looked wrong, it showed me right away which rule caused it.

Bias can show up even in a tiny system like this. Most genres have only one song, so a fan of a small genre gets one good match and then a list of guesses, while pop fans get three good matches. Real apps have the same kind of problem at a much bigger scale: whatever has the most data or the most clicks tends to get recommended the most.

Read the full write-up in [**the model card**](model_card.md).
