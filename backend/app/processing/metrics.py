import re

def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))

def token_estimate(text: str) -> int:
    # Deliberately labeled estimate; this is not a model tokenizer.
    return round(len(text.split()) * 1.33) if text.strip() else 0

def calculate_metrics(original: str, cleaned: str, summary: str, statements: list[dict], duplicate_result: dict, corrections: list[dict], chunks: list[dict], exported_text: str = "") -> dict:
    ow, sw = word_count(original), word_count(summary)
    return {
        "original_word_count": ow, "cleaned_word_count": word_count(cleaned),
        "exact_duplicates_removed": duplicate_result["exact_duplicates_removed"],
        "near_duplicates_identified": len(duplicate_result["near_duplicates"]),
        "statements_retained": sum(1 for s in statements if not s.get("duplicate_of")),
        "topics_identified": len(set(s["category"] for s in statements)),
        "correction_candidates": len(corrections),
        "unresolved_conflicts": sum(1 for c in corrections if c.get("review_status") in {"pending_review", "unresolved"}),
        "chunks_generated": len(chunks), "summary_word_count": sw,
        "original_token_estimate": token_estimate(original), "summary_token_estimate": token_estimate(summary),
        "exported_output_token_estimate": token_estimate(exported_text or summary),
        "word_reduction_percent": round((ow-sw)/ow*100, 2) if ow else 0.0,
        "token_reduction_percent": round((token_estimate(original)-token_estimate(summary))/token_estimate(original)*100, 2) if token_estimate(original) else 0.0,
        "token_estimate_method": "rough estimate: whitespace word count × 1.33; not an actual tokenizer",
    }
