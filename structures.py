from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PollCreateRequest(BaseModel):
    title: str = Field(..., description="Question of Poll")
    description: str = Field(..., description="Description of Poll")
    options: list[str] = Field(..., description="Options")

class AnswerRequest(BaseModel):
    answer: str = Field(..., description="Answer Variant in Plain Text")
    pollId: str = Field(..., description="ID of Poll we answer to")
    userId: str = Field(..., description="ID of User answering")

class Answer(BaseModel):
    id: str
    userId: str
    pollId: str
    answer: str
    createdAt: datetime
