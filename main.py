from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import asyncio
import json
import os
from pydantic import BaseModel
from models import *
from services import *
from controllers import *
import uvicorn

def create_app():
    app = FastAPI(title="Quorum Back Local")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # Initialize services
    db_service: DatabaseService = DatabaseService("sqlite+aiosqlite:///./test.db")
    auth_service: AuthService = AuthService(db_service)

    # Initialize controllers
    main_controller: MainController = MainController(db_service , auth_service)
    auth_controller: AuthController = AuthController(auth_service, db_service)

    # Register routes
    app.include_router(main_controller.router, prefix="")
    app.include_router(auth_controller.router, prefix="")

    @app.on_event("startup")
    async def startup():
        await db_service.create_database_tables()

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)