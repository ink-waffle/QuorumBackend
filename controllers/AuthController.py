from fastapi import HTTPException, Header
from datetime import timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from .basecontroller import BaseController
from services import *
import pytz

class AuthController(BaseController):
    def __init__(self, auth_service: AuthService, database_service: DatabaseService):
        self.auth = auth_service
        self.db = database_service
        super().__init__()

    def register_routes(self):
        self.router.add_api_route(
            "/auth/getUserIdWeak",
            self.getUserIdWeak,
            methods=["GET"],
            # response_model=TokenResponse
        )
        self.router.add_api_route(
            "/auth/markUserStrong",
            self.markUserStrong,
            methods=["GET"],
            response_model=bool
        )

    async def getUserIdWeak(self, requestId: str):
        # Get user from database
        resp = await self.auth.get_userIdWeak(requestId=requestId)
        return resp
    async def markUserStrong(self, userId: str):
        # Get user from database
        resp = await self.auth.markUserStrong(userId=userId)
        return resp