from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path
import os


_env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(_env_path)


class Settings(BaseSettings):
    WEBSHARE_API: str = os.environ['WEBSHARE_API']


settings = Settings(_case_sensitive=False)
