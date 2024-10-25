import asyncio
import datetime
from contextlib import asynccontextmanager

import fastapi_users
import uvicorn
from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Optional
import json
from starlette.middleware.cors import CORSMiddleware  # NEW

from src.api.auth import auth_backend, fastapi_users, current_user
from src.api.provider import ApiOrm
from src.api.schemas import FilterResponse, FilterRequest, filters
from src.data.crud import UpdateManager
from src.data.models import User
from src.data.schemas import SportDTO, UserRead, UserCreate
from src.parser import parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.create_task(parser.run_parser())
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "https://www.swaeger.com",
    "https://swaeger.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get('/')
async def get_match(filters: FilterRequest = Depends(), user: User = Depends(current_user)):
    matches = await ApiOrm.get_match_with_change(filters=filters)
    return matches


@app.get('/filters', response_model=FilterResponse)
async def get_filters(user: User = Depends(current_user)):
    return filters


@app.get('/match/{match_id}')
async def get_point_change(match_id: int, user: User = Depends(current_user)):
    changes = await ApiOrm.get_point_change(match_id=match_id)
    return changes


@app.get('/history/{team_name}')
async def get_team_history(team_name: str, current_match_id: int, user: User = Depends(current_user)):
    team_info = await ApiOrm.get_match_history_by_team_name(team_name=team_name, current_match_id=current_match_id)
    return team_info


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
