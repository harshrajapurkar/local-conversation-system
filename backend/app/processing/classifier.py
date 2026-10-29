import re

RULES = {
    "Corrections and Updates": [r"\bactually\b", r"\bcorrection\b", r"\bi meant\b", r"\binstead of\b", r"\bnot .+\b", r"\bchanged to\b", r"\bmoved to\b", r"\bincorrect\b"],
    "Tasks and Actions": [r"\bwill\b", r"\bmust\b", r"\bneed to\b", r"\bshould\b", r"\bcomplete\b", r"\btest\b", r"\bprepare\b", r"\bsubmit\b", r"\bowner\b"],
    "Deadlines and Scheduling": [r"\bdeadline\b", r"\bdue\b", r"\bby (monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2})\b", r"\b(at|on) \d{1,2}(:\d{2})?\s*(am|pm)?\b", r"\bmeeting\b", r"\bscheduled\b", r"\bmoved to\b"],
    "Decisions and Plans": [r"\bdecided\b", r"\bwe will use\b", r"\bplan to\b", r"\bgoing to\b", r"\bselected\b", r"\bchosen\b"],
    "Preferences and Requirements": [r"\bprefer\b", r"\bi want\b", r"\brequirement\b", r"\bmust not\b", r"\bshould not\b", r"\bavoid\b"],
    "Questions and Unresolved Issues": [r"\?", r"\bnot sure\b", r"\bunresolved\b", r"\bunclear\b", r"\bdoes anyone know\b"],
}

def classify(text: str) -> list[str]:
    labels = [category for category, patterns in RULES.items() if any(re.search(p, text, re.I) for p in patterns)]
    if not labels:
        labels = ["Facts and Reference Information"]
    return labels
