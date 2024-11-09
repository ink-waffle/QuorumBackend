from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, String, DateTime, Table, ForeignKey
from datetime import datetime
from typing import Optional, List

class Base(AsyncAttrs, DeclarativeBase):
    pass

# Answer association table that stores the actual answers
answer_table = Table(
    'answers',
    Base.metadata,
    Column('id', String, primary_key=True),
    Column('user_id', String, ForeignKey('users.id')),
    Column('poll_id', String, ForeignKey('polls.id')),
    Column('answer', String, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    fingerprintId = Column(String)
    ipaddress = Column(String)
    strongfingerprintId = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to polls through answers
    answered_polls = relationship("PollModel", secondary=answer_table, back_populates="respondents", lazy="selectin")

class PollModel(Base):
    __tablename__ = "polls"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationship to users through answers
    respondents = relationship("UserModel", secondary=answer_table, back_populates="answered_polls", lazy="selectin")