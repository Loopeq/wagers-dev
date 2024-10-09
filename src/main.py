import asyncio
import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Optional
import json
from starlette.middleware.cors import CORSMiddleware  # NEW
from src.api.provider import ApiOrm
from src.api.schemas import FilterResponse, FilterRequest, filters
from src.data.crud import UpdateManager, create_tables
from src.parser import parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await asyncio.create_task(parser.run_parser())
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def get_match(filters: FilterRequest = Depends()):
    matches = await ApiOrm.get_match_with_change(filters=filters)
    return matches


@app.get('/filters', response_model=FilterResponse)
async def get_filters():
    return filters


@app.get('/{match_id}')
async def get_point_change(match_id: int):
    changes = await ApiOrm.get_point_change(match_id=match_id)
    return changes


@app.get('/history/{team_name}')
async def get_team_history(team_name: str, current_match_id: int):
    team_info = await ApiOrm.get_match_history_by_team_name(team_name=team_name, current_match_id=current_match_id)
    return team_info

