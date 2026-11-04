# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Intended Use

**Goal / task:** VibeMatch suggests songs from a small catalog that fit a listener's taste. You give it a taste profile (favorite genre, favorite mood, target energy, and a few optional extras). It gives back the top songs, each with the reasons for its score.

**Assumptions it makes about the user:**

- The user can say what genre, mood and energy they want.
- One profile is enough to describe their taste.
- Taste does not change over time or with the situation.

**Intended use:** classroom exploration. It is a way to see how a basic content-based recommender turns data into a ranked list.

**Not intended for:**

- Real users or a real music app. The catalog is 25 invented songs.
- Deciding which artists get exposure, since it has no idea what is fair to artists.
- Anything where a wrong suggestion matters. It is a toy.

---

## 3. How the Model Works

Imagine a judge listening to every song in the catalog one at a time. For each song, the judge hands out points based on how well it fits the listener.

- If the genre is the one the listener asked for, the song gets 2 points.
- If the mood is the one they asked for, it gets 1 point.
- For energy, the closer the song is to the energy the listener wants, the more points it gets, up to 1 point. A song with exactly the right energy gets the full point. A song that is far off gets almost nothing. Too loud and too quiet are punished the same.
- If the listener also named things like tempo, how acoustic the song is, popularity, release decade or a detailed mood tag, those add smaller points the same way: closer is better. If the listener did not name something, it is simply skipped.

After judging every song, the system sorts them from highest to lowest and shows the top few. Every point is written down as a reason, so the output says things like "genre match: pop (+2.00)".

**Ranking modes.** The same judge can be told to care about different things. `balanced` is the default. `genre_first` makes genre worth 4 points, `mood_first` makes mood worth 3, and `energy_focused` makes energy worth 3. Only the point values change.

**Diversity penalty.** Optionally, after picking the best song, the system picks the next one while taking points away from any song whose artist or genre is already in the list. This is done one pick at a time, and the penalty is shown in the reasons.

**Changes from the starter code:** the starter only had empty placeholders. I wrote the CSV loader, the scoring rule, the ranking function and the explanations, added five new song columns, the ranking modes, the diversity penalty and the table output.

---

## 4. Data

- **Size:** 25 songs. The starter had 10, and I added 15.
- **Columns:** title, artist, genre, mood, energy, tempo (bpm), valence, danceability, acousticness, plus five I added: popularity (0 to 100), release decade, a detailed mood tag, instrumentalness and speechiness.
- **Genres (19):** pop, indie pop, lofi, ambient, country, rock, jazz, synthwave, hip-hop, edm, classical, r&b, metal, reggae, folk, latin, blues, punk, soul. Pop, lofi, ambient and country have more than one song. The other 15 genres have exactly one.
- **Moods (12):** happy, chill, intense, sad, peaceful, relaxed, aggressive, energetic, moody, focused, nostalgic, romantic.
- **Limits:** the songs and artists are made up. Nothing in the data reflects what real people listen to. There are no lyrics, no languages, no regional music scenes, and no listening history. Most genres have a single song, so a fan of those genres has almost nothing to be matched with.

---

## 5. Strengths

- It works well when the profile names a genre, a mood and an energy, and the catalog has several songs that fit. The Chill Lofi profile put the three lofi songs at the top, then the chill ambient song, and the quiet acoustic songs it picked felt right.
- The extra columns help. The Nostalgic Throwback profile gave one very clear winner, Golden Hour Groove, with a score of 5.47 because it matched on every feature. It also pulled in Dusty Porch Song, a country song that genre and mood alone would never have found, because of the "nostalgic" tag and the decade.
- It is easy to see why a song ranked where it did. Every result lists the exact points behind its score.

---

## 6. Limitations and Bias

**The weakness I found:** genre is worth so many points that it can overpower everything else. The clearest example is the "Conflicted" profile: a blues fan who wants sad songs at energy 0.9. Blues plus sad adds up to 3.0 points, and that is more than any song can earn from energy alone. So the top result was Rainy Highway Blues, a slow song with energy 0.4, and the actual high-energy songs (Storm Runner, Fuego Nocturno) ended up in fourth and fifth place with under 1 point each. The system never notices that the profile contradicts itself, and it keeps trusting the genre label.

Other things I noticed:

- **Small genres.** 15 of the 19 genres have one song. A rock fan gets one real match (Storm Runner, 4.48) and then a list of guesses based on mood and energy. Pop fans have three real matches. So the system treats users unequally depending on how popular their genre is in the catalog.
- **Exact text matching.** "indie pop" gets nothing for a "pop" fan, and "relaxed" gets nothing for a "chill" fan, even though a person would call those close. That caused odd results: a sad blues song showed up in the Chill Lofi top five just because its energy and acousticness were close.
- **Energy has no direction.** Being 0.1 too loud and 0.1 too quiet are scored the same.
- **Filter bubble.** Anyone who names a genre keeps getting that genre first, so they are never nudged toward something new.

**How the diversity penalty helps with fairness.** Without it, one artist or one genre can fill several of the top slots. In the Chill Lofi test, LoRoom took two of the top three spots and lofi took three of the top five. With the penalty on (0.5 for repeating an artist, 0.5 for repeating a genre), the second LoRoom song lost points and Spacewalk Thoughts, by a different artist, moved ahead of it. A small artist with one song now has a better chance of showing up, and the listener sees more variety. The penalty is a nudge, not a guarantee: a very strong match still gets through.

---

## 7. Evaluation

**Profiles tested (8):** Default Pop/Happy, High-Energy Pop, Chill Lofi, Deep Intense Rock, Nostalgic Throwback, and three edge cases (Conflicted sad + high energy, Genre not in the catalog, Mood only with no genre). The full outputs are in the README.

**What I looked for:** whether the top songs matched what the profile asked for, and whether the reasons added up to the score.

**What surprised me:**

- Gym Hero kept showing up for people who only wanted happy pop. It is a pop song, so it gets the 2 genre points, and its energy is high, which is close to what those users asked for. The only thing it misses is the mood ("intense" instead of "happy"), and that costs it just 1 point. A happy song from another genre, like Rooftop Lights, matches on mood and energy but gets no genre points, so it scores 1.96 against Gym Hero's 2.87.
- Gym Hero also showed up in second place for the Deep Intense Rock profile, even though it is not rock. It matches the "intense" mood and has nearly the same energy as the target.
- A sad blues song landed in the Chill Lofi top five.

**Profile-by-profile comparisons**

- *Default Pop/Happy vs High-Energy Pop:* nearly the same list. Only the top two traded places, because asking for energy 0.9 and a happier valence favors Neon Confetti (energy 0.88, valence 0.92) over Sunrise City.
- *Default Pop/Happy vs Chill Lofi:* no songs in common. One wants loud, bright pop. The other wants quiet, acoustic lofi at about half the energy.
- *Default Pop/Happy vs Deep Intense Rock:* only Gym Hero is in both. It is the one song that is pop, intense and high energy, so it bridges the two.
- *Default Pop/Happy vs Nostalgic Throwback:* four of five songs overlap because both want "happy". The throwback list moves Golden Hour Groove (a 1970s soul song) to first and brings in Dusty Porch Song, because that profile also asks for an older decade and a nostalgic feel.
- *High-Energy Pop vs Chill Lofi:* opposite ends. No overlap at all.
- *High-Energy Pop vs Deep Intense Rock:* both want very high energy but different moods and genres. Gym Hero is again the only shared song. The rock list is heavier (metal, hip-hop, EDM), and the pop list stays bright and happy.
- *High-Energy Pop vs Nostalgic Throwback:* four songs overlap. The throwback list has lower energy and likes older songs, so the soul song comes first.
- *Chill Lofi vs Deep Intense Rock:* opposite energy (0.38 against 0.92), so there is no overlap. The lofi list is quiet and acoustic, and the rock list is loud and fast.
- *Chill Lofi vs Nostalgic Throwback:* no overlap. The throwback profile wants warm, mid-energy, older songs, not quiet lofi.
- *Deep Intense Rock vs Nostalgic Throwback:* no overlap. Energy 0.92 against 0.6, and aggressive against happy-nostalgic.
- *Conflicted vs Deep Intense Rock:* both ask for energy near 0.9, but the rock list is all high energy and the conflicted list starts with a slow blues song. That is the genre-and-mood points beating the energy target.
- *Genre Not In Catalog (k-pop) vs Default Pop/Happy:* the same happy pop songs come back, but Gym Hero disappears because without a genre match its "intense" mood earns nothing. The top score drops from 3.98 to 1.94, which shows that it is falling back to mood and energy only.
- *Mood Only (peaceful) vs Chill Lofi:* both are quiet, and Spacewalk Thoughts and Library Rain appear in both. The mood-only list starts with classical and ambient songs, because there is no lofi genre pulling the lofi songs up.

**Experiments**

- *Weight shift (genre 2.0 to 1.0, energy 1.0 to 2.0):* the top two were unchanged, but Gym Hero dropped from third to fourth behind Rooftop Lights. For someone who asked for "happy", that feels more right to me. The change made the list more accurate, not just different.
- *Ranking modes:* genre-first keeps Gym Hero in third place with a big score. Mood-first and energy-focused both let Rooftop Lights take third instead.
- *Diversity penalty:* described in section 6. It changed the order of positions 2 to 4 in the Chill Lofi list.

**Three example explanations (in words)**

1. *Sunrise City for pop / happy / 0.8:* it scored 3.98. It is a pop song (+2.00), its mood is happy (+1.00), and its energy of 0.82 is almost exactly the 0.8 asked for (+0.98).
2. *Gym Hero for pop / happy / 0.8:* it scored 2.87. It is a pop song (+2.00) and its energy of 0.93 is fairly close to 0.8 (+0.87). Its mood is "intense", so it gets nothing for mood.
3. *Dusty Porch Song for Nostalgic Throwback:* it scored 2.00 even though it is country, not soul. It has the "nostalgic" mood tag (+0.50), its energy of 0.45 is not far from 0.6 (+0.85), its popularity of 60 is near 70 (+0.45), and its decade (2000) is not too far from 1970 (+0.20).

**Automated tests:** 8 tests pass. They check the CSV loads with numbers converted, that scoring returns a score and reasons, that a closer energy scores higher, that results come back sorted and limited to k, that the modes change the winner, and that the diversity penalty spreads out artists.

---

## 8. Future Work

- **Fuzzy matching for genre and mood.** Give partial credit to neighbors, so "indie pop" earns some points for a "pop" fan and "relaxed" earns some for "chill".
- **Catch contradictory profiles.** If the target energy is far from the energy of every song in the favorite genre and mood, warn the user or lower the genre weight.
- **A bigger, more balanced catalog.** At least a few songs per genre, so that fans of small genres get real matches.
- **Learning from behavior.** Let skips and replays slowly adjust the profile, the way real apps combine content-based and collaborative signals.

---

## 9. Personal Reflection

**Biggest learning moment.** I did not write a rule that says "show Gym Hero to happy pop fans", but it kept happening. The reason was that I gave genre 2 points and mood only 1. That made me realize the weights are where the taste of a recommender really lives. Changing one number moved songs around the whole list.

**How AI helped, and when I double-checked it.** I used Claude inside VS Code to plan the project, write most of the code, and draft the docs. I did not just trust it. I ran the program and the tests myself, and I worked a few scores out by hand (for example Sunrise City: 2.0 + 1.0 + 0.98 = 3.98). Along the way a few things had to be fixed: the starter `main.py` imported the recommender in a way that broke `python -m src.main`, plain `pytest` could not find the `src` folder until a `pytest.ini` was added, and the table was dropping trailing zeros (3.40 showed as 3.4) until number parsing was turned off.

**What surprised me.** How little it takes for a simple scoring rule to feel like a real recommendation. With just a few point values and a sort, the lists looked like something a music app might show, and the reasons made it feel even more believable. It was easy to forget that it is only adding up points.

**What I would try next.** Fuzzy matching so close genres and moods get partial credit, a warning when a profile contradicts itself, and a bigger catalog so every genre has real matches. After that, I would try letting skips and replays slowly change the profile.
