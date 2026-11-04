from src.recommender import (
    Song, UserProfile, Recommender, load_songs, score_song, recommend_songs,
)

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


POP_PREFS = {"genre": "pop", "mood": "happy", "energy": 0.8}


def test_load_songs_converts_numbers():
    songs = load_songs("data/songs.csv")

    assert len(songs) >= 20
    assert isinstance(songs[0]["energy"], float)
    assert isinstance(songs[0]["tempo_bpm"], float)
    assert isinstance(songs[0]["popularity"], int)


def test_score_song_returns_score_and_reasons():
    songs = load_songs("data/songs.csv")
    sunrise = next(s for s in songs if s["title"] == "Sunrise City")

    score, reasons = score_song(POP_PREFS, sunrise)

    assert score > 3.0
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)
    assert any("energy" in r for r in reasons)


def test_closer_energy_scores_higher():
    near = {"genre": "x", "mood": "x", "energy": 0.8}
    far = {"genre": "x", "mood": "x", "energy": 0.2}

    assert score_song({"energy": 0.8}, near)[0] > score_song({"energy": 0.8}, far)[0]


def test_recommend_songs_sorted_and_limited():
    songs = load_songs("data/songs.csv")

    results = recommend_songs(POP_PREFS, songs, k=4)
    scores = [score for _, score, _ in results]

    assert len(results) == 4
    assert scores == sorted(scores, reverse=True)
    assert all(explanation for _, _, explanation in results)


def test_modes_change_the_ranking_weights():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "rock", "mood": "happy", "energy": 0.8}

    genre_first = recommend_songs(prefs, songs, k=1, mode="genre_first")[0][0]
    mood_first = recommend_songs(prefs, songs, k=1, mode="mood_first")[0][0]

    assert genre_first["genre"] == "rock"
    assert mood_first["mood"] == "happy"


def test_diversity_penalty_spreads_out_artists():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.38}

    plain = recommend_songs(prefs, songs, k=3)
    varied = recommend_songs(prefs, songs, k=3, artist_penalty=1.5)

    plain_artists = [song["artist"] for song, _, _ in plain]
    varied_artists = [song["artist"] for song, _, _ in varied]
    assert len(set(plain_artists)) == 2   # LoRoom shows up twice without a penalty
    assert len(set(varied_artists)) == 3
