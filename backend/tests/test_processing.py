import pytest
from app.processing.pipeline import process_conversation
from app.processing.duplicates import normalize
from app.processing.corrections import detect_corrections
from app.processing.chunking import chunk_statements
from app.processing.metrics import calculate_metrics, word_count

SAMPLE = """The team meeting is planned for Wednesday at 2 PM.
Priya will complete the database schema.
The final submission deadline is Saturday.
Actually, the team meeting has been moved to Thursday at 4 PM.
Rahul will test the registration page.
The API documentation must be ready by Thursday.
The API documentation must be ready by Friday, not Thursday."""

def test_pipeline_preserves_key_tasks_and_flags_corrections():
    r = process_conversation(SAMPLE)
    texts = [s["text"] for s in r["statements"]]
    assert any("Priya" in t for t in texts)
    assert any("Rahul" in t for t in texts)
    assert any("Saturday" in t for t in texts)
    pairs = [(c["earlier_statement"], c["newer_statement"]) for c in r["summary"]["corrections"]]
    assert any("team meeting" in a.lower() and "Thursday" in b for a,b in pairs)
    assert any("API documentation" in a and "Friday" in b for a,b in pairs)
    assert all(c["review_status"] == "pending_review" for c in r["summary"]["corrections"])

def test_unrelated_tasks_not_flagged_as_correction():
    statements = [{"id":1,"index":0,"text":"Priya will complete the database schema."},{"id":2,"index":1,"text":"Rahul will test the registration page."}]
    assert detect_corrections(statements) == []

def test_different_events_with_dates_not_flagged():
    statements = [{"id":1,"index":0,"text":"The team meeting is on Wednesday."},{"id":2,"index":1,"text":"The final submission deadline is Saturday."}]
    assert detect_corrections(statements) == []

def test_duplicate_casefold_normalization():
    assert normalize("Hello, WORLD!") == normalize("hello world")

def test_empty_input_and_chunk_validation():
    with pytest.raises(ValueError): process_conversation("   ")
    with pytest.raises(ValueError): chunk_statements([], 0)

def test_long_statement_not_lost_by_chunking():
    items = [{"id":1,"index":0,"text":"one two three four five"},{"id":2,"index":1,"text":"six seven"}]
    chunks = chunk_statements(items, 3)
    assert sum(len(c["statements"]) for c in chunks) == 2
    assert chunks[0].get("oversized_statement") is True

def test_zero_word_metrics_safe():
    assert word_count("") == 0
