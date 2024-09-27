import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from typing import List
import json

from sqlalchemy import event
from starlette.middleware.cors import CORSMiddleware  # NEW

from src.api.api_methods import ApiOrm
from src.data.crud import UpdateManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: list[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#
#     @staticmethod
#     async def send_personal_message(message: str, websocket: WebSocket):
#         await websocket.send_text(message)
#
#     async def broadcast(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)
#
#
# manager = ConnectionManager()


@app.get('/')
async def get_point_change_base(hours: int):
    changes = await ApiOrm.get_point_changes()
    changes_serial = [{'match_id': change[0],
                       'old_point': change[1],
                       'new_point': change[2],
                       'period': change[3],
                       'bet_type': change[4],
                       'start_time': change[5],
                       'created_at': change[6],
                       'home_name': change[7],
                       'home_id': change[8],
                       'away_name': change[9],
                       'away_id': change[10],
                       'league_name': change[11]
                       } for change in changes]
    return changes_serial


@app.get('/{match_id}')
async def get_point_change_info(match_id: int):
    changes = await UpdateManager.get_point_change_info(match_id)
    return changes


async def run_server():
    config = uvicorn.Config('server:app', reload=True)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())
