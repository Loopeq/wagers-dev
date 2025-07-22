from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from src.core.settings import settings


def lifespan_factory():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    return lifespan


def create_application(router: APIRouter, **kwargs: Any) -> FastAPI:
    origins = [
        "https://www.swaeger.com",
        "https://swaeger.com",
        "http://87.228.114.236:8080",
    ]
    if settings.DEV == '1':
        for port in range(8010, 8200):
            origins.append(f'http://localhost:{port}')

    lifespan = lifespan_factory()
    application = FastAPI(lifespan=lifespan, **kwargs)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    application.include_router(router)
    return application
