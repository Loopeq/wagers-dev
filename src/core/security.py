from datetime import timedelta, datetime, timezone

from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.core.crud.api.user import UserOrm
from src.core.utils import verify_password
from src.core.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/v1/login')

SECRET_KEY = settings.AUTH_SECRET
ALGORITHM = settings.AUTH_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.AUTH_EXPIRE_TOKEN_HOURS * 60


async def authenticate_user(
        uuid: uuid.UUID, password: str, session: AsyncSession
):
    user = await UserOrm.get_user_by_uuid(uuid, session)
    if user is None:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
