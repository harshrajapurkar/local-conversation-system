import re
from difflib import SequenceMatcher
from typing import Callable

CUES = ("actually", "correction:", "i meant", "instead of", "not thursday", "not friday", "has changed to", "changed to", "has been moved", "moved to", "that information was incorrect", "rather than")
STOP = {"the", "a", "an", "is", "are", "was", "were", "to", "by", "on", "at", "for", "of", "and", "or", "will", "must", "be", "has", "have", "been", "it", "this", "that", "actually", "not", "instead", "from", "with", "we", "i", "me", "my", "our", "their", "his", "her", "planned", "scheduled", "deadline", "moved", "changed"}

def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.casefold()) if len(w) > 1 and w not in STOP}

def subject_similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    overlap = len(ta & tb) / len(ta | tb)
    # Shared named/topic terms are more meaningful than dates alone.
    no_dates_a = re.sub(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", "", a.casefold())
    no_dates_b = re.sub(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", "", b.casefold())
    text_sim = SequenceMatcher(None, no_dates_a, no_dates_b).ratio()
    return max(overlap, text_sim * 0.8)

def explicit_cue(text: str) -> bool:
    low = text.casefold().strip()
    return any(low.startswith(cue) or cue in low for cue in CUES)

def detect_corrections(statements: list[dict], nli_predictor: Callable | None = None, context_window: int = 8) -> list[dict]:
    events = []
    for new_pos, new in enumerate(statements):
        new_text = new["text"]
        cue = explicit_cue(new_text)
        candidates = []
        for old in statements[max(0, new_pos-context_window):new_pos]:
            old_text = old["text"]
            similarity = subject_similarity(old_text, new_text)
            # A correction cue is not enough: require evidence that the subject/event matches.
            if similarity < (0.16 if cue else 0.36):
                continue
            # Avoid unrelated task pairs with shared generic terms.
            old_tokens, new_tokens = tokens(old_text), tokens(new_text)
            shared = old_tokens & new_tokens
            if len(shared) < 1:
                continue
            score = None
            method = "rule_based_subject_and_cue" if cue else "rule_based_possible_conflict"
            event_type = "explicit_correction_candidate" if cue else "possible_revision_or_conflict"
            if nli_predictor:
                try:
                    score = nli_predictor(old_text, new_text)
                    if score.get("contradiction", 0) >= 0.65:
                        event_type = "possible_revision_or_conflict"
                        method = "local_nli_and_subject_match"
                    elif not cue:
                        continue
                except Exception:
                    method += "_nli_fallback"
            if not cue and similarity < 0.48:
                continue
            candidates.append((similarity, old, score, method, event_type))
        if candidates:
            similarity, old, score, method, event_type = max(candidates, key=lambda x: x[0])
            events.append({
                "earlier_statement_id": old["id"], "newer_statement_id": new["id"],
                "earlier_statement": old["text"], "newer_statement": new_text,
                "original_statement_index": old.get("index", old["id"]), "new_statement_index": new.get("index", new["id"]),
                "detection_method": method, "contradiction_confidence": (score or {}).get("contradiction") if score else None,
                "event_type": event_type, "review_status": "pending_review", "human_review_required": True,
                "subject_similarity": round(similarity, 3), "resolution": None,
            })
    return events
