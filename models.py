from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
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