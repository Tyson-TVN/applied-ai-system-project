# Genre and Activity Guide

This is the small knowledge base the assistant searches before it picks songs. Each section is one activity, feeling or genre family. The `Keywords` line is what the retriever matches against, and the `Profile hint` line is a starting taste profile that the planner can use. Genres and moods in the hints only use values that exist in `data/songs.csv`.

## Studying and homework
Keywords: study, studying, homework, exam, exams, reading, read, library, revise, revision, school, college, class, notes
Music for studying works best when it stays in the background. Low to medium energy, few or no vocals and a steady beat help people concentrate. Lofi and ambient are the usual picks; loud or very danceable songs pull attention away.
Profile hint: genre=lofi; mood=focused; energy=0.40; acousticness=0.75

## Deep focus and coding
Keywords: focus, focused, concentrate, concentration, coding, code, programming, work, working, productive, deadline, office
For long focus sessions people tend to like instrumental tracks with a repeating groove. Lofi beats and synthwave loops are common choices. Energy can be a little higher than for reading, but lyrics and sudden changes are distracting.
Profile hint: genre=lofi; mood=focused; energy=0.45

## Workout and gym
Keywords: workout, gym, lifting, lift, exercise, training, run, running, jog, jogging, cardio, sprint, pump, hype, fitness
Workout music needs high energy and a fast, steady tempo, usually 120 beats per minute or more. Intense or energetic moods keep motivation up. Pop, EDM, hip-hop and rock all work; very slow or acoustic songs do not.
Profile hint: mood=intense; energy=0.90; tempo_bpm=130; danceability=0.8

## Party and dancing
Keywords: party, dance, dancing, club, celebrate, celebration, friends, birthday, weekend, fun, banger, bangers
Party songs are about danceability and positive energy. People want songs they can move to, with high valence (they sound happy) and a strong beat. Pop, EDM and latin are safe bets.
Profile hint: mood=energetic; energy=0.85; danceability=0.9; valence=0.85

## Sleep and winding down
Keywords: sleep, sleeping, bed, bedtime, night, nighttime, late, insomnia, wind, calm, calming, quiet, soft, gentle
Before sleep, slower and quieter is better. Very low energy, slow tempo and mostly instrumental songs help. Classical and ambient fit best. Avoid anything with heavy drums or speech.
Profile hint: genre=ambient; mood=peaceful; energy=0.20; tempo_bpm=60; acousticness=0.9

## Chill and relaxing
Keywords: chill, chilled, relax, relaxing, relaxed, lazy, sunday, unwind, mellow, easy, laid, cozy, cosy, coffee, cafe
Relaxing music sits in the low to medium energy range and sounds warm. Jazz, lofi and reggae are good for this. It should feel easy and not demand attention.
Profile hint: mood=relaxed; energy=0.40; acousticness=0.7

## Sad or heartbroken
Keywords: sad, sadness, cry, crying, heartbreak, heartbroken, breakup, lonely, alone, miss, grief, down, depressed, blue, melancholy, melancholic, rainy, rain
When someone is sad they often want music that matches the feeling first, not music that tries to cheer them up. Slow, acoustic songs with low valence work well. Folk, blues and country have the most songs like this.
Profile hint: mood=sad; energy=0.35; valence=0.3; acousticness=0.8

## Happy and upbeat
Keywords: happy, upbeat, cheerful, sunny, sunshine, bright, positive, smile, joy, feel-good, uplifting, morning, wake
Feel-good music has high valence and medium-high energy. Pop, indie pop and soul are the strongest matches in the catalog. Morning playlists usually live here too.
Profile hint: genre=pop; mood=happy; energy=0.75; valence=0.85

## Road trip and driving
Keywords: road, trip, roadtrip, drive, driving, car, highway, travel, cruise, cruising, night drive
Driving music is steady and medium-high in energy, with a groove that keeps going. Synthwave is made for night drives. Rock and pop work for daytime trips.
Profile hint: genre=synthwave; mood=moody; energy=0.70; tempo_bpm=110

## Angry or venting
Keywords: angry, anger, mad, rage, furious, vent, venting, frustrated, stress, stressed, scream, heavy, loud, aggressive
Some people deal with anger by playing loud, aggressive music. Metal and punk are the most intense in the catalog, with very high energy and fast tempos.
Profile hint: mood=aggressive; energy=0.95; tempo_bpm=165

## Romantic and date night
Keywords: romantic, romance, love, date, dinner, candle, valentine, partner, slow, sensual, smooth
Romantic music is smooth and warm, usually medium energy with a relaxed groove. R&B and soul are the best fits, with jazz as a backup.
Profile hint: genre=r&b; mood=romantic; energy=0.55

## Nostalgia and throwbacks
Keywords: nostalgia, nostalgic, throwback, old, oldies, classic, retro, vintage, memories, 70s, 80s, 90s, childhood
Nostalgic listeners want older songs or songs that sound old. Soul and blues from the 1970s and country from the 2000s carry that feeling in this catalog.
Profile hint: mood=nostalgic; release_decade=1980; energy=0.5

## Pop and indie pop
Keywords: pop, indie, catchy, radio, hits, mainstream, chart
Pop songs are catchy, bright and usually high in popularity and danceability. Indie pop is similar but a little rawer. Both lean happy.
Profile hint: genre=pop; mood=happy; energy=0.8

## Lofi and ambient
Keywords: lofi, lo-fi, beats, ambient, atmospheric, background, instrumental, spacey, dreamy
Lofi is relaxed hip-hop-style beats, mostly instrumental. Ambient is even softer, with almost no beat. Both are background music.
Profile hint: genre=lofi; mood=chill; energy=0.35; acousticness=0.8

## Rock, metal and punk
Keywords: rock, guitar, guitars, metal, punk, headbang, mosh, band, riffs
These are the loud, guitar-driven genres. Rock is intense, metal is aggressive and heavy, punk is fast and defiant. All three are high energy.
Profile hint: genre=rock; mood=intense; energy=0.9; tempo_bpm=150

## Hip-hop and rap
Keywords: hip-hop, hiphop, hip, hop, rap, rapper, bars, beats, flow
Hip-hop has strong beats and a lot of spoken lyrics (high speechiness). Songs in the catalog are intense and very danceable.
Profile hint: genre=hip-hop; mood=intense; energy=0.8; danceability=0.85

## EDM and electronic
Keywords: edm, electronic, techno, house, rave, festival, drop, bass, synth
EDM is built for big rooms: very high energy, steady 128 bpm beats and euphoric drops. Synthwave is the moodier, retro side of electronic music.
Profile hint: genre=edm; mood=energetic; energy=0.95; tempo_bpm=128

## Jazz, soul and R&B
Keywords: jazz, soul, r&b, rnb, groove, smooth, saxophone, piano, funk
These genres are warm and groove-based. Jazz in the catalog is relaxed and cozy, soul is happy and nostalgic, and R&B is romantic.
Profile hint: genre=jazz; mood=relaxed; energy=0.45

## Country, folk and blues
Keywords: country, folk, blues, acoustic, storytelling, guitar, banjo, campfire, porch
These are acoustic, story-driven genres. Most of their songs in the catalog are slow and sad or nostalgic.
Profile hint: genre=country; mood=nostalgic; energy=0.45; acousticness=0.8

## Latin and reggae
Keywords: latin, reggaeton, salsa, spanish, reggae, island, beach, summer, tropical, vacation
Latin songs in the catalog are energetic and very danceable. Reggae is relaxed and sunny. Both have high valence and fit summer and beach moods.
Profile hint: genre=latin; mood=energetic; energy=0.85; valence=0.85

## Classical
Keywords: classical, orchestra, orchestral, piano, symphony, violin, calm, elegant
Classical music in the catalog is quiet, slow and fully instrumental. It is good for sleep, reading and calm moments.
Profile hint: genre=classical; mood=peaceful; energy=0.2; acousticness=0.95
