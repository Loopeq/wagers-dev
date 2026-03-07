from datetime import timedelta, datetime, timezone

from fastapi import HTTPException, Request, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crud.api.user import UserOrm
from src.core.utils import verify_password
from src.core.settings import settings

SECRET_KEY = settings.AUTH_SECRET
ALGORITHM = settings.AUTH_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.AUTH_EXPIRE_TOKEN_HOURS * 60


async def authenticate_user(email: str, password: str, session: AsyncSession):
    user = await UserOrm.get_user_by_email(email, session)
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


def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_key")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return token
