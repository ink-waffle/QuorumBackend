from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import HTTPException, status
import pytz
import aiohttp
import asyncio
from .DatabaseService import *
import traceback

class AuthService:
    def __init__(
        self,
        database_service: DatabaseService
    ):
        self.database_service: DatabaseService = database_service
        # Standard exceptions
        self.credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def get_userIdWeak(
        self,
        requestId: str
    ) -> str:
        url = f"https://eu.api.fpjs.io/events/{requestId}"
        headers = {
            "Auth-API-Key": "LhhFTuYss01k72LWvOA3",
            "accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                try:
                    resp = await response.json()
                    fingerprintId = resp["products"]["identification"]["data"]["visitorId"]
                    ipaddress = resp["products"]["identification"]["data"]["ip"]
                    user = await self.database_service.find_and_update_user(
                        fingerprint_id=fingerprintId,
                        ipaddress=ipaddress
                        )
                    if not user:
                        user = await self.database_service.create_user(
                            fingerprint_id=fingerprintId,
                            ipaddress=ipaddress
                        )
                    return user.id
                except Exception as e:
                    print(traceback.format_exc())
    
    async def markUserStrong(
        self,
        userId: str
    ) -> bool:
        return await self.database_service.mark_user_strong(user_id=userId)