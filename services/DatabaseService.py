from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_, not_, insert
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator, Dict
from datetime import datetime
from models import Base, UserModel, PollModel, answer_table
import uuid

class DatabaseService:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url)
        self.AsyncSessionLocal = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_database_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise
    
    async def find_user_by_fingerprint_or_ip(
        self,
        fingerprint_id: Optional[str] = None,
        ipaddress: Optional[str] = None
    ) -> Optional[UserModel]:
        if not fingerprint_id and not ipaddress:
            raise ValueError("Either fingerprint_id or ipaddress must be provided")
            
        async with self.session() as session:
            # Build query conditions
            conditions = []
            if fingerprint_id:
                conditions.append(UserModel.fingerprintId == fingerprint_id)
            if ipaddress:
                conditions.append(UserModel.ipaddress == ipaddress)
                
            # Use OR to match either condition
            result = await session.execute(
                select(UserModel).filter(or_(*conditions))
            )
            return result.scalar_one_or_none()
    
    # User-related methods
    async def get_user(self, user_id: str) -> Optional[UserModel]:
        async with self.session() as session:
            result = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )
            return result.scalar_one_or_none()

    async def create_user(self, fingerprint_id: str, ipaddress: str) -> UserModel:
        async with self.session() as session:
            user = UserModel(
                id=str(uuid.uuid4())[:8],
                fingerprintId=fingerprint_id,
                ipaddress=ipaddress
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    # Poll-related methods
    async def create_poll(
        self,
        title: str,
        description: str
    ) -> PollModel:
        async with self.session() as session:
            poll = PollModel(
                id=str(uuid.uuid4())[:8],
                title=title,
                description=description
            )
            session.add(poll)
            await session.commit()
            await session.refresh(poll)
            return poll

    async def get_poll(self, poll_id: str) -> Optional[PollModel]:
        async with self.session() as session:
            result = await session.execute(
                select(PollModel).filter(PollModel.id == poll_id)
            )
            return result.scalar_one_or_none()

    async def get_all_polls(self) -> List[PollModel]:
        async with self.session() as session:
            result = await session.execute(select(PollModel))
            return result.scalars().all()

    async def close_poll(self, poll_id: str) -> Optional[PollModel]:
        async with self.session() as session:
            result = await session.execute(
                select(PollModel).filter(PollModel.id == poll_id)
            )
            poll = result.scalar_one_or_none()
            if poll:
                poll.closed_at = datetime.utcnow()
                await session.commit()
                await session.refresh(poll)
                return poll
            raise ValueError("Poll not found")

    # Answer-related methods
    async def submit_answer(
        self,
        user_id: str,
        poll_id: str,
        answer: str
    ) -> Dict:
        async with self.session() as session:
            # Check if poll exists
            poll_result = await session.execute(
                select(PollModel).filter(PollModel.id == poll_id)
            )
            if not poll_result.scalar_one_or_none():
                raise ValueError("Poll not found")

            # Check if user exists
            user_result = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )
            if not user_result.scalar_one_or_none():
                raise ValueError("User not found")

            # Check if user has already answered this poll
            existing_answer = await session.execute(
                select(answer_table).where(
                    and_(
                        answer_table.c.user_id == user_id,
                        answer_table.c.poll_id == poll_id
                    )
                )
            )
            if existing_answer.first():
                raise ValueError("User has already answered this poll")

            # Insert new answer
            answer_id = f"answer_{datetime.utcnow().timestamp()}"
            await session.execute(
                insert(answer_table).values(
                    id=answer_id,
                    user_id=user_id,
                    poll_id=poll_id,
                    answer=answer,
                    created_at=datetime.utcnow()
                )
            )
            await session.commit()
            
            return {
                "id": answer_id,
                "user_id": user_id,
                "poll_id": poll_id,
                "answer": answer
            }

    async def get_poll_answers(self, poll_id: str) -> List[Dict]:
        async with self.session() as session:
            # First check if poll exists
            poll_result = await session.execute(
                select(PollModel).filter(PollModel.id == poll_id)
            )
            if not poll_result.scalar_one_or_none():
                raise ValueError("Poll not found")

            result = await session.execute(
                select(answer_table).where(answer_table.c.poll_id == poll_id)
            )
            return [dict(row) for row in result.all()]

    async def get_user_answers(self, user_id: str) -> List[Dict]:
        async with self.session() as session:
            # First check if user exists
            user_result = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )
            if not user_result.scalar_one_or_none():
                raise ValueError("User not found")

            result = await session.execute(
                select(answer_table).where(answer_table.c.user_id == user_id)
            )
            return [dict(row) for row in result.all()]

    async def get_user_poll_answer(
        self,
        user_id: str,
        poll_id: str
    ) -> Optional[Dict]:
        async with self.session() as session:
            result = await session.execute(
                select(answer_table).where(
                    and_(
                        answer_table.c.user_id == user_id,
                        answer_table.c.poll_id == poll_id
                    )
                )
            )
            row = result.first()
            return dict(row) if row else None