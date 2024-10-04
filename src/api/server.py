import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Optional
import json

from sqlalchemy import event
from starlette.middleware.cors import CORSMiddleware  # NEW

from src.api.api_methods import ApiOrm

from src.api.schemas import FilterResponse, FilterRequest, filters
from src.data.crud import UpdateManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, jsn: dict):
        for connection in self.active_connections:
            await connection.send_json(jsn)


manager = ConnectionManager()


@app.get('/')
async def get_match_on_change_base(filters: FilterRequest = Depends()):
    matches = await ApiOrm.get_match_with_change(filters=filters)
    return matches


@app.get('/filters', response_model=FilterResponse)
async def get_filters():
    return filters


@app.get('/{match_id}')
async def get_point_change_info(match_id: int):
    changes = await ApiOrm.get_point_change(match_id=match_id)
    return changes


@app.get('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def run_server():
    config = uvicorn.Config('server:app', reload=True)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())
