from typing import Annotated

from sqlalchemy import String
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.settings import settings


async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=False
)

async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

str_256 = Annotated[str, 256]
str_128 = Annotated[str, 128]
str_64 = Annotated[str, 64]


class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }
