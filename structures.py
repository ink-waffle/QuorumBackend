from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TokenModel(BaseModel):
    access_token: str
    token_type: str

class Credentialsodel(BaseModel):
    username: str
    password: str

class TradeRequest(BaseModel):
    direction: int = Field(..., description="Trade direction: 'up' or 'down'")
    amount: float = Field(..., gt=0, description="Trade amount")
    duration_seconds: int = Field(..., gt=0, le=60, description="Trade duration in seconds")
    asset_name: str = Field(..., description="Asset index")

class Trade(BaseModel):
    id: str
    user_id: str
    direction: int
    amount: float
    entry_time: datetime
    duration: float
    result: Optional[str]
    payout: Optional[float]

class Balance(BaseModel):
    balance: float