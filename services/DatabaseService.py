from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_, not_
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator
from datetime import datetime
from models import Base, UserModel, PollModel, AnswerModel
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

    # User-related methods
    async def get_user(self, user_id: str) -> Optional[UserModel]:
        async with self.session() as session:
            result = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )
            return result.scalar_one_or_none()

    async def find_and_update_user(
        self,
        fingerprint_id: Optional[str] = None,
        ipaddress: Optional[str] = None
    ) -> Optional[UserModel]:
        if not fingerprint_id and not ipaddress:
            raise ValueError("Either fingerprint_id or ipaddress must be provided")
            
        async with self.session() as session:
            conditions = []
            if fingerprint_id:
                conditions.append(UserModel.fingerprintId == fingerprint_id)
            if ipaddress:
                conditions.append(UserModel.ipaddress == ipaddress)
                
            result = await session.execute(
                select(UserModel).filter(or_(*conditions))
            )
            user = result.scalar_one_or_none()
            
            if user:
                update_data = {}
                if fingerprint_id and user.fingerprintId != fingerprint_id:
                    update_data['fingerprintId'] = fingerprint_id
                if ipaddress and user.ipaddress != ipaddress:
                    update_data['ipaddress'] = ipaddress
                    
                if update_data:
                    for key, value in update_data.items():
                        setattr(user, key, value)
                    await session.commit()
                    await session.refresh(user)
            
            return user

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
        description: str,
        options: list[str]
    ) -> PollModel:
        async with self.session() as session:
            poll = PollModel(
                id=str(uuid.uuid4())[:8],
                title=title,
                description=description,
                options=options
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

    async def get_unanswered_polls(self, user_id: str) -> List[PollModel]:
        async with self.session() as session:
            
            # Get all polls that don't have an answer from this user
            answered_polls = select(AnswerModel.poll_id).where(
                AnswerModel.user_id == user_id
            ).scalar_subquery()

            result = await session.execute(
                select(PollModel)
                .where(PollModel.id.not_in(answered_polls))
                .where(or_(
                    PollModel.closed_at.is_(None),
                    PollModel.closed_at > datetime.utcnow()
                ))
                .order_by(PollModel.created_at.desc())
            )
            
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
    async def create_answer(
        self,
        user_id: str,
        poll_id: str,
        answer: str
    ) -> AnswerModel:
        async with self.session() as session:
            # Check if user has already answered
            existing = await session.execute(
                select(AnswerModel).filter(
                    and_(
                        AnswerModel.user_id == user_id,
                        AnswerModel.poll_id == poll_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("User has already answered this poll")

            # Verify user and poll exist
            user = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )
            if not user.scalar_one_or_none():
                raise ValueError("User not found")

            poll = await session.execute(
                select(PollModel).filter(PollModel.id == poll_id)
            )
            if not poll.scalar_one_or_none():
                raise ValueError("Poll not found")

            answer_model = AnswerModel(
                id=f"answer_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                poll_id=poll_id,
                answer=answer
            )
            session.add(answer_model)
            await session.commit()
            await session.refresh(answer_model)
            return answer_model

    async def get_poll_answers(self, poll_id: str) -> List[AnswerModel]:
        async with self.session() as session:
            result = await session.execute(
                select(AnswerModel)
                .filter(AnswerModel.poll_id == poll_id)
                .order_by(AnswerModel.created_at.desc())
            )
            return result.scalars().all()

    async def get_user_answers(self, user_id: str) -> List[AnswerModel]:
        async with self.session() as session:
            result = await session.execute(
                select(AnswerModel)
                .filter(AnswerModel.user_id == user_id)
                .order_by(AnswerModel.created_at.desc())
            )
            return result.scalars().all()

    async def get_user_poll_answer(
        self,
        user_id: str,
        poll_id: str
    ) -> Optional[AnswerModel]:
        async with self.session() as session:
            result = await session.execute(
                select(AnswerModel).filter(
                    and_(
                        AnswerModel.user_id == user_id,
                        AnswerModel.poll_id == poll_id
                    )
                )
            )
            return result.scalar_one_or_none()