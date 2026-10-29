"""Optional lazy-loaded local NLI predictor. Disabled unless ENABLE_LOCAL_NLI=1."""
import os
from functools import lru_cache

MODEL_NAME = os.getenv("LOCAL_NLI_MODEL", "cross-encoder/nli-deberta-v3-xsmall")

@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(MODEL_NAME, device="cpu")

def get_nli_predictor():
    if os.getenv("ENABLE_LOCAL_NLI", "0").strip().lower() not in {"1", "true", "yes"}:
        return None
    try:
        _load_model()
        return predict_relationship
    except Exception:
        # Model packages/cache/download may be unavailable. Rule-based path remains usable.
        return None

def predict_relationship(premise: str, hypothesis: str) -> dict:
    model = _load_model()
    raw = model.predict([(premise, hypothesis)], convert_to_numpy=True)[0]
    labels = getattr(model.model.config, "id2label", {}) or {}
    result = {"contradiction": 0.0, "entailment": 0.0, "neutral": 0.0}
    # Softmax when returned values look like logits; otherwise normalize positive scores.
    import math
    values = [float(x) for x in raw]
    exp = [math.exp(max(-40.0, min(40.0, x - max(values)))) for x in values]
    total = sum(exp) or 1.0
    probs = [x / total for x in exp]
    for idx, prob in enumerate(probs):
        label = str(labels.get(idx, labels.get(str(idx), ""))).lower()
        for canonical in result:
            if canonical in label:
                result[canonical] = prob
    return result
