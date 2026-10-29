import re
from difflib import SequenceMatcher
from .preprocess import Statement


def normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.casefold()).strip()


def detect_duplicates(statements: list[Statement], threshold: float = 0.90) -> dict:
    exact_removed = 0
    near = []
    seen: dict[str, int] = {}
    for s in statements:
        key = normalize(s.text)
        if key in seen:
            s.duplicate_of = seen[key]
            exact_removed += 1
            continue
        seen[key] = s.id
    retained = [s for s in statements if s.duplicate_of is None]
    for i, current in enumerate(retained):
        for previous in retained[:i]:
            ratio = SequenceMatcher(None, normalize(previous.text), normalize(current.text)).ratio()
            if threshold <= ratio < 1.0:
                current.near_duplicate = True
                near.append({"statement_id": current.id, "similar_to": previous.id, "similarity": round(ratio, 3), "text": current.text, "matched_text": previous.text})
                break
    return {"exact_duplicates_removed": exact_removed, "near_duplicates": near, "retained_statements": [s for s in statements if s.duplicate_of is None]}
