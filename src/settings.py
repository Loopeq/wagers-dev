from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path
import os


_env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(_env_path)


class Settings(BaseSettings):
    WEBSHARE_API: str = os.environ['WEBSHARE_API']

    @property
    def DATABASE_URL(self):
        if int(os.environ['AMVERA']):
            host = 'amvera-senya-std-cnpg-wagers-db-rw'
        else:
            host = 'localhost'
        print(host)
        return (f"postgresql+asyncpg://{os.environ['DB_USER']}:"
                f"{os.environ['DB_PASS']}@{host}:5432/{os.environ['DB_NAME']}")


settings = Settings(_case_sensitive=False)
