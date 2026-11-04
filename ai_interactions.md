# AI Interactions Log

This file covers the two stretch features that need it: extra song attributes built with an AI agent, and the design pattern behind the ranking modes.

---

## Agentic Workflow (SF8)

**What task did you give the agent?**

I gave Claude (running as an agent inside VS Code, with access to the project folder and the terminal) the whole assignment and asked it to build the recommender. That included five new song attributes (popularity, release decade, a detailed mood tag, instrumentalness, speechiness), and updating the scoring so it actually uses them. Before any code was written, it analyzed the project and I approved a written plan.

**Prompts used:**

- "Analyze the project... do the project yourself as much as you can" (with the full assignment and the grading rubric pasted in), followed by approving the plan it wrote.
- Follow-up messages: pasting the output of my `pip install` run so it could confirm the environment was ready, and giving it the path to my cloned folder.
- The step in the approved plan covering the new attributes (not a separate prompt): "Add 5+ attributes (popularity 0-100, release decade, detailed mood tag, instrumentalness, speechiness) to `data/songs.csv`, make sure the CSV loads without errors, and make the scoring use them only when the user profile asks for them."

**What did the agent generate or change?**

- `data/songs.csv`: grew from 10 to 25 songs, with 5 new columns filled in for every row.
- `src/recommender.py`: wrote `load_songs` (converts numbers), `score_song` (returns score and reasons), `recommend_songs` (scores everything, sorts, returns top k), the ranking modes, the diversity re-ranking, and the `Recommender` class used by the tests. New `Song` fields have default values so the original tests still work.
- `src/main.py`: eight profiles, a table output using `tabulate`, mode switching, and the experiments.
- `tests/test_recommender.py`: six new tests. `pytest.ini` and `requirements.txt` were also updated.
- `README.md`, `model_card.md`, and this file.

**What did you verify or fix manually?**

- Ran `pytest` (8 tests) and `python -m src.main` and read through every table.
- Worked a few scores out by hand to check the math (Sunrise City = 2.0 + 1.0 + 0.98 = 3.98; Gym Hero = 2.0 + 0.87 = 2.87).
- Things that had to be fixed along the way:
  - The starter `main.py` used `from recommender import ...`, which breaks `python -m src.main`. It now uses `from src.recommender import ...`.
  - Plain `pytest` could not find the `src` package. Adding `pytest.ini` with `pythonpath = .` fixed it.
  - `tabulate` printed 3.40 as 3.4. Setting `disable_numparse=True` fixed it.
  - A test for the diversity penalty first had a weak "or" in its assertion. It was tightened so it checks exactly what the data shows.
- Checked that the new attributes are really used: the Nostalgic Throwback profile ranks Dusty Porch Song fifth only because of its mood tag, popularity and decade.

---

## Design Pattern (SF10)

**Which design pattern did you use?**

A simple Strategy pattern. The "strategy" is a set of weights, stored as data in a dictionary (`SCORING_MODES`), not as separate classes.

**How did AI help you brainstorm or implement it?**

The assignment asked for several ranking strategies (genre-first, mood-first, energy-focused) that a user can switch between, and the plan Claude wrote for it was to do this without copying the scoring code. Its reasoning was that the strategies only differ in their numbers, so the scoring function can stay the same and just take a `mode` argument. That avoids a class per strategy and avoids `if mode == ...` branches inside the scoring code. A custom dictionary of weights can also be passed straight in, which I used for the weight-shift experiment.

**How does the pattern appear in your final code?**

- `SCORING_MODES` in `src/recommender.py` holds one weight dictionary per mode: `balanced`, `genre_first`, `mood_first`, `energy_focused`.
- `score_song(user_prefs, song, mode)` and `recommend_songs(..., mode=...)` look the weights up and apply them. Nothing else changes between modes.
- In `src/main.py`, `--mode` picks the strategy for the profile runs (`python -m src.main --mode genre_first`), and a separate section prints the same profile under every mode so the differences are visible.
