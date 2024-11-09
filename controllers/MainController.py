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
            methods=["GET"]
        )
        
        self.router.add_api_route(
            "/getUnansweredPolls",
            self.getUnansweredPolls,
            methods=["GET"]
        )
        
        self.router.add_api_route(
            "/getPoll",
            self.getPoll,
            methods=["GET"]
        )
        
        self.router.add_api_route(
            "/createPoll",
            self.createPoll,
            methods=["POST"]
        )
        
        
    async def getUserAnswers(
        self,
        userId: str
    ):
        return await self.database_service.get_user_answers(userId)
    
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
    ):
        polls = await self.database_service.get_unanswered_polls(userId)
        return polls
    
    async def getPoll(
        self,
        pollId: str
    ):
        poll = await self.database_service.get_poll(pollId)
        return poll
    
    async def createPoll(
        self,
        pollCreateReq: PollCreateRequest
    ):
        poll = await self.database_service.create_poll(
            title=pollCreateReq.title,
            description=pollCreateReq.description,
            options=pollCreateReq.options
        )
        return poll
        