from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path
import os


_env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(_env_path)


class Settings(BaseSettings):
    WEBSHARE_API: str = os.environ['WEBSHARE_API']
    SECRET: str = os.environ['SECRET']
    RECOVERY_SECRET: str = os.environ['RECOVERY_SECRET']
    DEV: str = os.environ.get('DEV')

    @property
    def DATABASE_URL(self):
        return (f"postgresql+asyncpg://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:"
                f"{os.environ['DB_PORT']}/{os.environ['DB_NAME']}")


settings = Settings(_case_sensitive=False)

