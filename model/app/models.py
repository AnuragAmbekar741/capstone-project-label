from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Message(BaseModel):
    text: str
    timestamp: Optional[str] = None

class Thread(BaseModel):
    subject: Optional[str] = None
    messages: List[Message]
    mode: Optional[Literal["short","long"]] = "short"

class ThreadsPayload(BaseModel):
    threads: List[Thread]

class SummarizeResult(BaseModel):
    summary: str
    key_points: list[str] = []
    actions: list[str] = []
    dates: list[str] = []

class CategorizeResult(BaseModel):
    labels: list[str]
    rationale: str | None = None

class Suggestion(BaseModel):
    text: str
    tone: Optional[str] = "neutral"

class SuggestResult(BaseModel):
    suggestions: list[Suggestion]

class OnOffloadRequest(BaseModel):
    x_user_id: str = Field(..., description="Stable user hash ID")
