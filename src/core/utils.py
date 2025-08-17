from passlib.context import CryptContext
from src.core.constants import PERIODS
from src.parser.config import sports_ids
from datetime import timedelta, datetime
import secrets

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

def get_yesterday_ymd():
    yesterday_utc = datetime.utcnow() - timedelta(days=1)
    formatted = yesterday_utc.strftime('%Y-%m-%d')
    return formatted


def generate_invite_code(length: int = 12):
    return secrets.token_urlsafe(length)[:length]