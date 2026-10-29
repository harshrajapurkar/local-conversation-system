from .preprocess import clean_text, split_statements
from .duplicates import detect_duplicates
from .classifier import classify
from .corrections import detect_corrections
from .summarizer import build_summary
from .chunking import chunk_statements
from .metrics import calculate_metrics
from .nli import get_nli_predictor

IMPORTANT_HINTS = ("deadline", "due", "decided", "must", "will", "prefer", "password", "meeting", "submit", "project", "correction", "actually", "not ")

def process_conversation(text: str, compression: str = "balanced", max_chunk_words: int = 180, similarity_threshold: float = 0.90, context_window: int = 8) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Please enter a non-empty conversation.")
    if len(text) > 1_000_000:
        raise ValueError("Conversation is too large. Maximum supported input is 1,000,000 characters.")
    if compression not in {"low", "balanced", "high"}:
        raise ValueError("compression must be low, balanced, or high")
    if not 1 <= max_chunk_words <= 10000:
        raise ValueError("max_chunk_words must be between 1 and 10000")
    cleaned = clean_text(text)
    raw = split_statements(cleaned)
    statements = [{"id": i+1, "text": item, "original_text": item, "index": i, "category": "Other Information", "duplicate_of": None, "near_duplicate": False, "important": any(h in item.casefold() for h in IMPORTANT_HINTS)} for i, item in enumerate(raw)]
    duplicate_result = detect_duplicates_objects(statements, similarity_threshold)
    for s in statements:
        s["category"] = classify(s["text"])[0]
    correction_events = detect_corrections([s for s in statements if not s.get("duplicate_of")], nli_predictor=get_nli_predictor(), context_window=context_window)
    summary = build_summary(statements, correction_events, compression=compression)
    compact_statements = [s for s in statements if not s.get("duplicate_of") and s["id"] not in summary["superseded_statement_ids"]]
    chunks = chunk_statements(compact_statements, max_chunk_words)
    metrics = calculate_metrics(text, cleaned, summary["summary_text"], statements, duplicate_result, correction_events, chunks)
    return {"original_text": text, "cleaned_text": cleaned, "statements": statements, "duplicates": {"exact_duplicates_removed": duplicate_result["exact_duplicates_removed"], "near_duplicates": duplicate_result["near_duplicates"]}, "summary": summary, "chunks": chunks, "metrics": metrics, "options": {"compression": compression, "max_chunk_words": max_chunk_words, "similarity_threshold": similarity_threshold, "context_window": context_window}}

def detect_duplicates_objects(statements, threshold):
    from .preprocess import Statement
    from .duplicates import detect_duplicates
    objects = [Statement(id=s["id"], text=s["text"], original_text=s["original_text"], index=s["index"]) for s in statements]
    result = detect_duplicates(objects, threshold)
    by_id = {obj.id: obj for obj in objects}
    for s in statements:
        obj = by_id[s["id"]]
        s["duplicate_of"] = obj.duplicate_of
        s["near_duplicate"] = obj.near_duplicate
    return {"exact_duplicates_removed": result["exact_duplicates_removed"], "near_duplicates": result["near_duplicates"]}
