from pydantic import BaseModel
from typing import Optional, List, Any

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    category_filter: Optional[str] = None

class QAQuery(BaseModel):
    question: str

class SearchResultResponse(BaseModel):
    url: str
    title: str
    source: str
    category: str
    published_at: str
    summary: str
    key_points: List[str]
    score: float

class QAAnswerResponse(BaseModel):
    answer: str
    sources: List[str]
    retrieved: List[dict]

class UsageUpdateRequest(BaseModel):
    count: int
