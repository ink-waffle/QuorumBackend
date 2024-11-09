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
            self.place_trade,
            methods=["POST"],
            response_model=Trade
        )
        
        self.router.add_api_route(
            "/checkTrade",
            self.check_trade,
            methods=["GET"],
            response_model=Trade
        )
        
        self.router.add_api_route(
            "/balance",
            self.get_balance,
            methods=["GET"],
            response_model=Balance
        )
        
    async def answerPoll(
        self, 
        userId: str,
        pollId: str,
        response: str,
        token: str = Header(...)):
        user_id = await self.auth.verify_token(token)
        trade = await self.trading_service.place_trade(
            user_id,
            trade_request.direction,
            trade_request.amount,
            trade_request.duration_seconds,
            trade_request.asset_name
        )
        return Trade(
            id=trade.id,
            user_id=trade.user[0].id,
            direction=trade.direction,
            amount=trade.amount,
            entry_time=trade.entry_time,
            duration=trade.duration,
            result="undef",
            payout=0
        )
        
    async def check_trade(
        self,
        trade_id: str,
        token: str = Header(...)
    ):
        user_id = await self.auth.verify_token(token)
        trade = await self.trading_service.check_trade(trade_id)
        return Trade(
            id=trade.id,
            user_id=trade.user[0].id,
            direction=trade.direction,
            amount=trade.amount,
            entry_time=trade.entry_time,
            duration=trade.duration,
            result=trade.result,
            payout=trade.payout
        )
        
    async def get_balance(
        self,
        token: str = Header(...)
    ):
        user_id = await self.auth.verify_token(token)
        balance = await self.balance_service.get_user_balance(user_id)
        return {"balance": balance}