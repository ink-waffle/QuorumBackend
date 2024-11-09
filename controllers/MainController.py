from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List
from services import *
from models import *
from structures import *
from .basecontroller import *


class MainController(BaseController):
    def __init__(
        self, 
        database_service: DatabaseService,
        auth_handler: AuthService):
        self.database_service : DatabaseService = database_service
        self.auth : AuthService = auth_handler
        super().__init__()
        
    def register_routes(self):
        # Create the dependency function once during route registration

        self.router.add_api_route(
            "/answerPoll",
            self.answerPoll,
            methods=["POST"]
        )
        
        self.router.add_api_route(
            "/getUserAnswers",
            self.getUserAnswers,
            methods=["GET"],
            response_model=list[Answer]
        )
        
        self.router.add_api_route(
            "/getUnansweredPolls",
            self.getUnansweredPolls,
            methods=["GET"],
            response_model=list[Poll]
        )
        
        self.router.add_api_route(
            "/getPoll",
            self.getPoll,
            methods=["GET"],
            response_model=Poll
        )
        
        self.router.add_api_route(
            "/createPoll",
            self.createPoll,
            methods=["POST"],
            response_model=Poll
        )
        self.router.add_api_route(
            "/getUserComments",
            self.getUserComments,
            methods=["GET"],
            response_model=list[Comment]
        )
        self.router.add_api_route(
            "/getPollThreads",
            self.getPollThreads,
            methods=["GET"],
            response_model=dict[str, list[Comment]]
        )
        self.router.add_api_route(
            "/createComment",
            self.createComment,
            methods=["POST"],
            response_model=Comment
        )
        self.router.add_api_route(
            "/getLeastRepliedThreadForUser",
            self.getLeastRepliedThreadForUser,
            methods=["GET"],
            response_model=list[Comment]
        )
        self.router.add_api_route(
            "/getCommentVotes",
            self.getCommentVotes,
            methods=["GET"],
            response_model=CommentVotes
        )
        self.router.add_api_route(
            "/getUserVoteOnComment",
            self.getUserVote,
            methods=["GET"],
            response_model=int
        )
        
        
    async def getUserAnswers(
        self,
        userId: str
    ):
        answers: list[AnswerModel] = await self.database_service.get_user_answers(userId)
        answerResponse = list()
        for answer in answers:
            answerResponse.append(Answer(
                id = answer.id,
                userId=answer.user_id,
                pollId=answer.poll_id,
                answer=answer.answer,
                createdAt=answer.created_at
            ))
        return answerResponse
    
    async def answerPoll(
        self,
        answerReq: AnswerRequest
    ):
        return await self.database_service.create_answer(
            user_id=answerReq.userId, 
            poll_id=answerReq.pollId, 
            answer=answerReq.answer
            )
        
    async def getUnansweredPolls(
        self,
        userId: str
    ) -> list[Poll]:
        polls = await self.database_service.get_unanswered_polls(userId)
        pollResponse = list()
        for poll in polls:
            answersResponse: list[Answer] = list()
            for answer in poll.answers:
                answersResponse.append(Answer(
                    id=answer.id,
                    userId=answer.user_id,
                    pollId=answer.poll_id,
                    answer=answer.answer,
                    createdAt=answer.created_at
                ))
            pollResponse.append(Poll(
                id=poll.id,
                title=poll.title,
                description=poll.description,
                options=poll.options,
                answers=answersResponse,
                comments={},
                requireVerification=poll.requireVerification,
                isActionable=poll.isActionable
            ))
        return pollResponse
    
    async def getPoll(
        self,
        pollId: str
    ) -> Poll:
        poll = await self.database_service.get_poll(pollId)
        
        answersResponse: list[Answer] = list()
        for answer in poll.answers:
            answersResponse.append(Answer(
                id=answer.id,
                userId=answer.user_id,
                pollId=answer.poll_id,
                answer=answer.answer,
                createdAt=answer.created_at,
            ))
        
        # commentResponse: list[Comment] = list()
        # for comment in poll.comments:
        #     commentResponse.append(Comment(
        #         id=comment.id,
        #         content=comment.content,
        #         pollAnswer=comment.poll_answer,
        #         userId=comment.user_id,
        #         pollId=comment.poll_id
        #     ))
        return Poll(
            id=poll.id,
            title=poll.title,
            description=poll.description,
            options=poll.options,
            answers=answersResponse,
            comments={},
            requireVerification=poll.requireVerification,
            isActionable=poll.isActionable
        )
    
    async def createPoll(
        self,
        pollCreateReq: PollCreateRequest
    ) -> Poll:
        poll = await self.database_service.create_poll(
            title=pollCreateReq.title,
            description=pollCreateReq.description,
            options=pollCreateReq.options,
            require_verification=pollCreateReq.requireVerification,
            is_actionable=pollCreateReq.isActionable
        )
        
        answersResponse: list[Answer] = list()
        for answer in poll.answers:
            answersResponse.append(Answer(
                id=answer.id,
                userId=answer.user_id,
                pollId=answer.poll_id,
                answer=answer.answer,
                createdAt=answer.created_at,
            ))
        return Poll(
            id=poll.id,
            title=poll.title,
            description=poll.description,
            options=poll.options,
            answers=answersResponse,
            comments={},
            requireVerification=pollCreateReq.requireVerification,
            isActionable=pollCreateReq.isActionable
        )
    
    async def getUserComments(
        self,
        userId: str) -> list[Comment]:
        comments: list[CommentModel] = await self.database_service.get_user_comments(userId)
        commentResponse = list()
        for comment in comments:
            commentResponse.append(Comment(
                id=comment.id,
                content=comment.content,
                pollAnswer=comment.poll_answer,
                userId=comment.user_id,
                pollId=comment.poll_id,
                threadId=comment.thread_id,
                createdAt=comment.created_at,
                threadPosition=comment.thread_position
            ))
        return commentResponse
        pass
    
    async def createComment(
        self,
        commentRequest: CommentCreateRequest
    ) -> Comment:
        answer = await self.database_service.get_user_poll_answer(
            user_id=commentRequest.userId,
            poll_id=commentRequest.pollId
        )
        comment = await self.database_service.create_comment(
            user_id=commentRequest.userId,
            poll_id=commentRequest.pollId,
            poll_answer=answer.answer,
            content=commentRequest.content,
            thread_id=commentRequest.threadId
        )
        return Comment(
            id=comment.id,
            content=comment.content,
            pollAnswer=comment.poll_answer,
            userId=comment.user_id,
            pollId=comment.poll_id,
            threadId=comment.thread_id,
            createdAt=comment.created_at,
            threadPosition=comment.thread_position
            )
    
    async def getPollThreads(
        self,
        pollId: str
    ):
        threads: dict = await self.database_service.get_poll_comments(
            poll_id=pollId,
            include_threads=True
        )
        threadResponse = dict()
        for thread_id, comments in threads.items():
            commentResponse = list()
            for comment in comments:
                commentResponse.append(Comment(
                    id=comment.id,
                    content=comment.content,
                    pollAnswer=comment.poll_answer,
                    userId=comment.user_id,
                    pollId=comment.poll_id,
                    threadId=comment.thread_id,
                    createdAt=comment.created_at,
                    threadPosition=comment.thread_position
                ))
            threadResponse[thread_id] = commentResponse
        return threadResponse
    
    async def getLeastRepliedThreadForUser(
        self,
        pollId: str,
        userId: str
    ) -> list[Comment]:
        answer: AnswerModel = await self.database_service.get_user_poll_answer(
            user_id=userId,
            poll_id=pollId
        )
        
        poll = await self.database_service.get_poll(poll_id=pollId)
        oppositeAnswer = ""
        for option in poll.options:
            if option != answer.answer:
                oppositeAnswer = answer.answer
                break
        
        thread: list[CommentModel] = await self.database_service.get_leastreplies_thread_by_answer(
            poll_id=pollId,
            answer=oppositeAnswer
            )
        
        commentResponse = list()
        for comment in thread.comments:
            commentResponse.append(Comment(
                id=comment.id,
                content=comment.content,
                pollAnswer=comment.poll_answer,
                userId=comment.user_id,
                pollId=comment.poll_id,
                threadId=comment.thread_id,
                createdAt=comment.created_at,
                threadPosition=comment.thread_position
            ))
        
        return commentResponse
    
    async def getUserVote(
        self,
        commentId: str,
        userId: str
    ) -> int:
        return await self.database_service.get_user_vote(
            user_id=userId,
            comment_id=commentId
        )
    
    async def getCommentVotes(
        self,
        commentId: str
    ):
        votes = await self.database_service.get_comment_votes(commentId)
        return CommentVotes(
            upvotes=votes["upvotes"],
            downvotes=votes["downvotes"],
            score=votes["score"]
        )
    async def voteComment(
        self,
        voteRequest: CommentVoteRequest
    ):
        comment = await self.database_service.vote_comment(
            user_id=voteRequest.userId,
            comment_id=voteRequest.commentId,
            vote_type=voteRequest.voteType
        )
        return Comment(
            id=comment.id,
            content=comment.content,
            pollAnswer=comment.poll_answer,
            userId=comment.user_id,
            pollId=comment.poll_id,
            threadId=comment.thread_id,
            createdAt=comment.created_at,
            threadPosition=comment.thread_position,
            )