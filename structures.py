from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List, Literal

class PollCreateRequest(BaseModel):
    title: str = Field(..., description="Question of Poll")
    description: str = Field(..., description="Description of Poll")
    options: list[str] = Field(..., description="Options")

class CommentCreateRequest(BaseModel):
    content: str = Field(..., description="Content of the comment")
    pollId: str = Field(..., description="ID of Poll we comment on")
    userId: str = Field(..., description="ID of User commenting")
    threadId: Optional[str] = Field(None, description="ID of thread to reply to. If not provided, creates new thread")

class Comment(BaseModel):
    id: str
    content: str
    pollAnswer: str
    userId: str
    pollId: str
    threadId: str
    threadPosition: int
    createdAt: datetime

class Answer(BaseModel):
    id: str
    userId: str
    pollId: str
    answer: str
    createdAt: datetime

class Poll(BaseModel):
    id: str
    title: str = Field(..., description="Question of Poll")
    description: str = Field(..., description="Description of Poll")
    options: list[str] = Field(..., description="Options")
    answers: list[Answer] = Field(..., description="answers")
    comments: Dict[str, List[Comment]] = Field(default={}, description="Comments grouped by thread_id")

class AnswerRequest(BaseModel):
    answer: str = Field(..., description="Answer Variant in Plain Text")
    pollId: str = Field(..., description="ID of Poll we answer to")
    userId: str = Field(..., description="ID of User answering")

class CommentThread(BaseModel):
    """Helper model for returning a full thread of comments"""
    threadId: str
    comments: List[Comment]
    pollId: str

class CommentVotes(BaseModel):
    upvotes: int
    downvotes: int
    score: int

class CommentVoteRequest(BaseModel):
    userId: str = Field(..., description="ID of User voting")
    commentId: str = Field(..., description="ID of Comment being voted on")
    voteType: Literal[1, -1] = Field(..., description="1 for upvote, -1 for downvote")