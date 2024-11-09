from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, UniqueConstraint
from datetime import datetime
from typing import Optional, List

class Base(AsyncAttrs, DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    strongfingerprintId = Column(String)
    fingerprintId = Column(String)
    ipaddress = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Only relationship is to answers
    answers = relationship("AnswerModel", back_populates="user", lazy="selectin")
    comments = relationship("CommentModel", back_populates="user", lazy="selectin")

class PollModel(Base):
    __tablename__ = "polls"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    options = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Only relationship is to answers
    answers = relationship("AnswerModel", back_populates="poll", lazy="selectin")
    comments = relationship("CommentModel", back_populates="poll", lazy="selectin")

class AnswerModel(Base):
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True, index=True)
    answer = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(String, ForeignKey('users.id'))
    poll_id = Column(String, ForeignKey('polls.id'))
    
    # Relationships
    user = relationship("UserModel", back_populates="answers")
    poll = relationship("PollModel", back_populates="answers")

class CommentModel(Base):
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True, index=True)
    poll_answer = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    thread_id = Column(String, nullable=False, index=True)  # Group comments in threads
    thread_position = Column(Integer, nullable=False)  # Position in thread for ordering
    
    # Vote counters
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    
    user_id = Column(String, ForeignKey('users.id'))
    poll_id = Column(String, ForeignKey('polls.id'))
    
    user = relationship("UserModel", back_populates="comments")
    poll = relationship("PollModel", back_populates="comments")
    votes = relationship("VoteModel", back_populates="comment")




class VoteModel(Base):
    __tablename__ = "comment_votes"
    
    id = Column(String, primary_key=True, index=True)
    vote_type = Column(Integer, nullable=False)  # 1 for upvote, -1 for downvote
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(String, ForeignKey('users.id'))
    comment_id = Column(String, ForeignKey('comments.id'))
    
    user = relationship("UserModel")
    comment = relationship("CommentModel", back_populates="votes")
    
    # Ensure one vote per user per comment
    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote'),
    )