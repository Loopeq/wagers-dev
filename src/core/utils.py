import logging

from passlib.context import CryptContext

from src.core.constants import PERIODS
from src.parser.config import sports_ids

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def format_key(key: str):
    return ';'.join(key.split(';')[:3])


def get_period_title(sport_id: int, key: str, relation: str | None):
    key = format_key(key)
    sport = PERIODS[sports_ids[sport_id].lower()]
    if relation:
        sport = sport.get(relation)
    return sport.get(key)
