from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from jwt import InvalidTokenError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.crud.api.user import UserOrm
from src.core.db.db_helper import db_helper
from src.core.schemas import TokenData, UserOut
from src.core.security import ALGORITHM, SECRET_KEY
from src.core.security import oauth2_scheme
from uuid import UUID


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uuid_str: str = payload.get("sub")
        if uuid_str is None:
            raise credentials_exception
        try:
            token_uuid = UUID(uuid_str)
        except:
            raise credentials_exception
        token_data = TokenData(uuid=token_uuid)
    except InvalidTokenError:
        raise credentials_exception
    user = await UserOrm.get_user_by_uuid(
        uuid=token_data.uuid, session=session
    )
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserOut, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


CURRENT_USER = Annotated[UserOut, Depends(get_current_user)]
CURRENT_ACTIVE_USER = Annotated[UserOut, Depends(get_current_active_user)]
