import re
from dataclasses import dataclass

@dataclass
class Statement:
    id: int
    text: str
    original_text: str
    index: int
    category: str = "Other Information"
    duplicate_of: int | None = None
    near_duplicate: bool = False


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Keep line and speaker structure; normalize spaces within each line.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def split_statements(text: str) -> list[str]:
    """Split on sentence-ending punctuation or newlines, retaining simple abbreviations reasonably well."""
    text = clean_text(text)
    if not text:
        return []
    chunks = re.split(r"\n+|(?<=[.!?])\s+(?=(?:[A-Z0-9\"'“‘(]|Actually|Correction|I meant|Not\b))", text)
    return [part.strip() for part in chunks if part.strip()]
