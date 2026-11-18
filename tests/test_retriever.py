from src.retriever import load_guide, parse_hint, retrieve, tokenize


def test_guide_loads_sections_with_hints():
    notes = load_guide()
    assert len(notes) >= 15
    assert all(note.keywords for note in notes)
    assert all(note.hint for note in notes)


def test_parse_hint_converts_numbers():
    assert parse_hint("genre=lofi; energy=0.40") == {"genre": "lofi", "energy": 0.4}


def test_tokenize_strips_plural():
    assert "beat" in tokenize("lofi beats")


def test_retrieve_finds_matching_activity():
    notes = load_guide()
    titles = [note.title for note, _ in retrieve("hype songs for the gym", notes)]
    assert titles[0] == "Workout and gym"


def test_retrieve_matches_phrases_and_returns_nothing_off_topic():
    notes = load_guide()
    assert any(n.title == "Road trip and driving" for n, _ in retrieve("a night drive", notes))
    assert retrieve("what is the capital of France", notes) == []
