from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_, not_, func
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator, Dict, Tuple, Literal
from datetime import datetime
from models import *
import uuid
import random
from fastapi import HTTPException, status

class DatabaseService:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url)
        self.AsyncSessionLocal = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.unallowed_Exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
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

    async def mark_user_strong(self, user_id: str):
        async with self.session() as session:
            result = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            user.strongfingerprintId = "ldskfhlkan29739akjs92"
            await session.commit()
            await session.refresh(user)
            return True
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
        options: list[str],
        require_verification: bool = False,
        is_actionable: bool = False
    ) -> PollModel:
        async with self.session() as session:
            poll = PollModel(
                id=str(uuid.uuid4())[:8],
                title=title,
                description=description,
                options=options,
                requireVerification=require_verification,
                isActionable=is_actionable
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
            user = (await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            )).scalar_one_or_none()

            poll = (await session.execute(
                select(PollModel).filter(PollModel.id == poll_id)
            )).scalar_one_or_none()
            
            # Check if user can answer this poll
            if poll.requireVerification and (not user.strongfingerprintId or user.strongfingerprintId == ""):
                return self.unallowed_Exception

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
    
    async def get_user_poll_answer(self, poll_id: str, user_id: str) -> AnswerModel:
        async with self.session() as session:
            result = await session.execute(
                select(AnswerModel)
                .filter(
                    and_(
                        AnswerModel.poll_id == poll_id,
                        AnswerModel.user_id == user_id,
                        )
                    )
                .order_by(AnswerModel.created_at.desc())
            )
            return result.scalar_one_or_none()

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

    async def create_comment(
        self,
        user_id: str,
        poll_id: str,
        poll_answer: str,
        content: str,
        thread_id: Optional[str] = None
    ) -> CommentModel:
        """
        Create a new comment. If thread_id is not provided, starts a new thread.
        If thread_id is provided, adds comment to existing thread.
        """
        async with self.session() as session:
            # If no thread_id provided, create new thread
            if not thread_id or thread_id == "":
                thread_id = str(uuid.uuid4())[:8]
                thread_position = 0
            else:
                # Verify thread exists and get next position
                thread_exists = await session.execute(
                    select(CommentModel).filter(CommentModel.thread_id == thread_id)
                )
                if not thread_exists.scalar_one_or_none():
                    raise ValueError("Thread not found")
                
                # Get the highest position in this thread
                max_position_result = await session.execute(
                    select(func.max(CommentModel.thread_position))
                    .filter(CommentModel.thread_id == thread_id)
                )
                max_position = max_position_result.scalar_one_or_none() or -1
                thread_position = max_position + 1

            comment = CommentModel(
                id=str(uuid.uuid4())[:8],
                content=content,
                user_id=user_id,
                poll_id=poll_id,
                poll_answer=poll_answer,
                thread_id=thread_id,
                thread_position=thread_position
            )
            
            session.add(comment)
            await session.commit()
            await session.refresh(comment)
            return comment

    async def get_poll_comments(
        self,
        poll_id: str,
        include_threads: bool = True
    ) -> list[dict[str, List[CommentModel]]]:
        """
        Get all comments for a poll.
        If include_threads is True, returns comments grouped by thread_id.
        If False, returns flat list of comments.
        """
        async with self.session() as session:
            # Get comments ordered by thread and position
            query = select(CommentModel).filter(
                CommentModel.poll_id == poll_id
            ).order_by(
                CommentModel.thread_id,
                CommentModel.thread_position
            )
            
            result = await session.execute(query)
            comments = result.scalars().all()

            if not include_threads:
                return comments

            # Group comments by thread
            threads = {}
            for comment in comments:
                if comment.thread_id not in threads:
                    threads[comment.thread_id] = []
                threads[comment.thread_id].append(comment)
            
            return threads

    async def get_comment_thread(self, thread_id: str) -> List[CommentModel]:
        """Get all comments in a specific thread, ordered by position."""
        async with self.session() as session:
            result = await session.execute(
                select(CommentModel)
                .filter(CommentModel.thread_id == thread_id)
                .order_by(CommentModel.thread_position)
            )
            comments = result.scalars().all()
            
            if not comments:
                raise ValueError("Thread not found")
                
            return comments
    
    async def get_comment_thread(self, thread_id: str) -> List[CommentModel]:
        """Get all comments in a specific thread, ordered by position."""
        async with self.session() as session:
            result = await session.execute(
                select(CommentModel)
                .filter(CommentModel.thread_id == thread_id)
                .order_by(CommentModel.thread_position)
            )
            comments = result.scalars().all()
            
            if not comments:
                raise ValueError("Thread not found")
                
            return comments

    async def get_random_thread_by_answer(
        self,
        poll_id: str,
        answer: str
    ) -> Optional[List[CommentModel]]:
        """
        Get a random thread from a poll where the parent comment (position 0)
        was made by a user who answered with the specified answer.
        
        Returns the complete thread (all comments) or None if no matching threads found.
        """
        async with self.session() as session:
            # First get all thread_ids where the parent comment has the specified answer
            parent_comments_query = (
                select(CommentModel.thread_id)
                .filter(and_(
                    CommentModel.poll_id == poll_id,
                    CommentModel.thread_position == 0,
                    CommentModel.poll_answer == answer
                ))
            )
            
            result = await session.execute(parent_comments_query)
            matching_thread_ids = result.scalars().all()
            
            if not matching_thread_ids:
                return None
            
            # Pick a random thread_id
            random_thread_id = random.choice(matching_thread_ids)
            
            # Get all comments in the selected thread
            thread_comments = await session.execute(
                select(CommentModel)
                .filter(CommentModel.thread_id == random_thread_id)
                .order_by(CommentModel.thread_position)
            )
            
            return thread_comments.scalars().all()
    
    async def get_leastreplies_thread_by_answer(
        self,
        poll_id: str,
        answer: str
    ) -> Optional[List[CommentModel]]:
        """
        Get a thread from a poll where:
        1. Parent comment (position 0) was made by a user who answered with the specified answer
        2. Thread has the least number of replies
        3. If multiple threads have same min replies, picks the oldest one
        
        Returns the complete thread (all comments) or None if no matching threads found.
        """
        async with self.session() as session:
            # First get all qualifying parent comments with their reply counts
            thread_counts = (
                select(
                    CommentModel.thread_id,
                    func.count(CommentModel.id).label('reply_count')
                )
                .filter(CommentModel.poll_id == poll_id)
                .group_by(CommentModel.thread_id)
                .subquery()
            )

            # Get parent comments that match our criteria
            parent_query = (
                select(CommentModel, thread_counts.c.reply_count)
                .join(
                    thread_counts,
                    CommentModel.thread_id == thread_counts.c.thread_id
                )
                .filter(and_(
                    CommentModel.poll_id == poll_id,
                    CommentModel.thread_position == 0,
                    CommentModel.poll_answer == answer
                ))
                # Order by reply count (ascending) and then creation time (ascending)
                .order_by(
                    thread_counts.c.reply_count.asc(),
                    CommentModel.created_at.asc()
                )
            )
            
            result = await session.execute(parent_query)
            first_result = result.first()
            
            if not first_result:
                return None
            
            parent_comment = first_result[0]
            
            # Get all comments in the selected thread
            thread_comments = await session.execute(
                select(CommentModel)
                .filter(CommentModel.thread_id == parent_comment.thread_id)
                .order_by(CommentModel.thread_position)
            )
            
            return thread_comments.scalars().all()
    
    
    async def get_user_comments(
        self,
        user_id: str
    ) -> List[CommentModel]:
        """Get all comments by a specific user."""
        async with self.session() as session:
            result = await session.execute(
                select(CommentModel)
                .filter(CommentModel.user_id == user_id)
                .order_by(CommentModel.created_at.desc())
            )
            return result.scalars().all()
    
        
    async def vote_comment(
        self,
        user_id: str,
        comment_id: str,
        vote_type: Literal[1, -1]  # 1 for upvote, -1 for downvote
    ) -> CommentModel:
        async with self.session() as session:
            
            user = await session.execute(
                select(UserModel).filter(UserModel.id == user_id)
            ).scalar_one_or_none()
            comment = await session.execute(
                select(CommentModel).filter(CommentModel.id == comment_id)
            ).scalar_one_or_none()
            
            # Check if user already voted
            existing_vote = await session.execute(
                select(VoteModel).filter(
                    and_(
                        VoteModel.user_id == user_id,
                        VoteModel.comment_id == comment_id
                    )
                )
            )
            existing_vote = existing_vote.scalar_one_or_none()

            if existing_vote:
                return comment

            else:
                # New vote
                new_vote = VoteModel(
                    id=str(uuid.uuid4())[:8],
                    user_id=user_id,
                    comment_id=comment_id,
                    vote_type=vote_type
                )
                session.add(new_vote)
                if vote_type == 1:
                    comment.upvotes += 1
                else:
                    comment.downvotes += 1
                await session.commit()
                return comment
    async def get_user_vote(
        self,
        user_id: str,
        comment_id: str
    ) -> Optional[int]:
        """Get user's vote on a comment. Returns 1, -1, or None."""
        async with self.session() as session:
            result = await session.execute(
                select(VoteModel).filter(
                    and_(
                        VoteModel.user_id == user_id,
                        VoteModel.comment_id == comment_id
                    )
                )
            )
            vote = result.scalar_one_or_none()
            return vote.vote_type if vote else 0


    async def get_comment_votes(
        self,
        comment_id: str
    ) -> Dict[str, int]:
        """Get vote counts for a comment."""
        async with self.session() as session:
            comment_result = await session.execute(
                select(CommentModel).filter(CommentModel.id == comment_id)
            )
            comment = comment_result.scalar_one_or_none()
            
            return {
                "upvotes": comment.upvotes,
                "downvotes": comment.downvotes,
                "score": comment.upvotes - comment.downvotes
            }