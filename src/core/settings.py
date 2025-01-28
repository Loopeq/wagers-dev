from uuid import UUID

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseSettings):
    WEBSHARE_API: str = os.environ['WEBSHARE_API']
    RAPID_KEY: str = os.environ['RAPID_KEY']
    DEV: str = os.environ.get('DEV')
    AUTH_SECRET: str = os.environ.get('AUTH_SECRET')
    AUTH_ALGORITHM: str = os.environ.get('AUTH_ALGORITHM')
    AUTH_EXPIRE_TOKEN_HOURS: int = os.environ.get('AUTH_EXPIRE_TOKEN_HOURS')
    FIRST_USER_UUID: UUID = os.environ.get('FIRST_USER_UUID')
    FIRST_USER_PASSWORD: str = os.environ.get('FIRST_USER_PASSWORD')

    @property
    def DATABASE_URL(self):
        return (f"postgresql+asyncpg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['DB_HOST']}:"
                f"{os.environ['DB_PORT']}/{os.environ['POSTGRES_DB']}")


settings = Settings(_case_sensitive=False)

