def chunk_statements(statements: list[dict], max_words: int = 180) -> list[dict]:
    if max_words < 1:
        raise ValueError("max_words must be at least 1")
    chunks, current, count = [], [], 0
    for statement in statements:
        words = len(statement["text"].split())
        if current and count + words > max_words:
            chunks.append({"chunk_index": len(chunks), "statements": current, "word_count": count})
            current, count = [], 0
        current.append({"id": statement["id"], "text": statement["text"], "source_index": statement["index"]})
        count += words
        if words > max_words:
            chunks.append({"chunk_index": len(chunks), "statements": current, "word_count": count, "oversized_statement": True})
            current, count = [], 0
    if current:
        chunks.append({"chunk_index": len(chunks), "statements": current, "word_count": count})
    return chunks
