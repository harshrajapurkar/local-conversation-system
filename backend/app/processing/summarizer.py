
from .classifier import classify

CATEGORY_ORDER = [
    "Decisions and Plans",
    "Tasks and Actions",
    "Facts and Reference Information",
    "Deadlines and Scheduling",
    "Preferences and Requirements",
    "Questions and Unresolved Issues",
    "Corrections and Updates",
    "Other Information",
]

IMPORTANT_CATEGORIES = {
    "Tasks and Actions",
    "Decisions and Plans",
    "Deadlines and Scheduling",
    "Corrections and Updates",
    "Questions and Unresolved Issues",
}


def _clean_text(text: str) -> str:
    """Normalize whitespace without changing the statement's meaning."""
    return " ".join(text.split()).strip()


def _unique_statements(statements: list[dict]) -> list[dict]:
    """Remove duplicate text while preserving the first occurrence."""
    result = []
    seen = set()

    for statement in statements:
        text = _clean_text(statement.get("text", ""))
        if not text:
            continue

        key = text.casefold()

        if statement.get("duplicate_of") or key in seen:
            continue

        seen.add(key)
        result.append({**statement, "text": text})

    return result


def build_summary(
    statements: list[dict],
    corrections: list[dict],
    resolutions: dict[int, str] | None = None,
    compression: str = "balanced",
) -> dict:
    resolutions = resolutions or {}

    # Do not modify the original correction dictionaries.
    correction_results = []
    superseded = set()

    for i, event in enumerate(corrections):
        updated_event = dict(event)

        status = resolutions.get(
            i,
            updated_event.get("review_status", "pending_review"),
        )

        if status not in {
            "accepted",
            "rejected",
            "unresolved",
            "pending_review",
        }:
            status = "pending_review"

        updated_event["review_status"] = status
        updated_event["resolution"] = (
            status if status in {"accepted", "rejected", "unresolved"} else None
        )

        if status == "accepted":
            earlier_id = updated_event.get("earlier_statement_id")
            if earlier_id is not None:
                superseded.add(earlier_id)

        correction_results.append(updated_event)

    # Keep all non-superseded, non-duplicate source statements.
    retained = [
        s for s in statements
        if s.get("id") not in superseded
        and not s.get("duplicate_of")
        and _clean_text(s.get("text", ""))
    ]

    retained = _unique_statements(retained)

    # High compression prioritizes important information.
    if compression == "high":
        retained = [
            s for s in retained
            if s.get("important")
            or s.get("category") in IMPORTANT_CATEGORIES
        ]

    # Group the retained statements by category.
    sections = {
        category: [
            s["text"]
            for s in retained
            if s.get("category") == category
        ]
        for category in CATEGORY_ORDER
    }

    # Preserve unexpected categories instead of silently losing them.
    for statement in retained:
        category = statement.get("category", "Other Information")
        if category not in sections:
            sections[category] = []

        if statement["text"] not in sections[category]:
            sections[category].append(statement["text"])

    topic_groups = {}

    for statement in retained:
        category = statement.get("category", "Other Information")
        topic_groups.setdefault(category, []).append({
            "id": statement.get("id"),
            "text": statement["text"],
            "source_index": statement.get("index"),
        })

    important_context = list(dict.fromkeys(
        statement["text"]
        for statement in retained
        if statement.get("important")
        or statement.get("category") in IMPORTANT_CATEGORIES
    ))

    pending = [
        event for event in correction_results
        if event["review_status"] in {"pending_review", "unresolved"}
    ]

    # Only include headings for categories that contain statements.
    summary_text = "\n".join(
    s["text"] for s in retained
    )
    """category + "\n" + "\n".join(
            f"- {text}" for text in texts
        )
        for category, texts in sections.items()
        if texts
    )"""

    return {
        "sections": sections,
        "topic_groups": topic_groups,
        "important_context": important_context,
        "corrections": correction_results,
        "pending_conflicts": pending,
        "superseded_statement_ids": sorted(superseded),
        "summary_text": summary_text,
    }
