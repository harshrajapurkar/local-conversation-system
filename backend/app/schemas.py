from pydantic import BaseModel, Field
from typing import Literal

class ProcessRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    title: str = Field(default="Untitled conversation", max_length=120)
    compression: Literal["low", "balanced", "high"] = "balanced"
    max_chunk_words: int = Field(default=180, ge=1, le=10000)
    similarity_threshold: float = Field(default=0.90, ge=0.5, le=0.99)
    context_window: int = Field(default=8, ge=1, le=50)
    save: bool = True

class ResolveRequest(BaseModel):
    status: Literal["accepted", "rejected", "unresolved"]
