from typing import List
from pydantic import BaseModel, Field


class AIAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)


class AISourceMetadata(BaseModel):
    title: str
    category: str


class AIAskResponse(BaseModel):
    answer: str
    sources: List[AISourceMetadata] = []
    grounded: bool
