from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crud.api.user import UserOrm
from src.core.db.db_helper import db_helper
from src.core.schemas import TokenData, UserOut
from src.core.security import ALGORITHM, SECRET_KEY, get_token_from_cookie



async def get_current_user(
    token: Annotated[str, Depends(get_token_from_cookie)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        sid: str = payload.get("sid")
        if not email:
            raise credentials_exception

        token_data = TokenData(email=email)

    except InvalidTokenError:
        raise credentials_exception

    user = await UserOrm.get_user_by_email(
        email=token_data.email,
        session=session
    )
    if user is None:
        raise credentials_exception

    if user.session_id != sid:
        raise HTTPException(status_code=401, detail="Session expired")
    
    return user


async def get_current_active_user(
    current_user: Annotated[UserOut, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(
    current_user: Annotated[UserOut, Depends(get_current_user)],
): 
    if current_user.superuser:
        return current_user
    raise HTTPException(status_code=403, detail="Permission denied")


CURRENT_USER = Annotated[UserOut, Depends(get_current_user)]
CURRENT_ACTIVE_USER = Annotated[UserOut, Depends(get_current_active_user)]
CURRENT_ADMIN_USER = Annotated[UserOut, Depends(get_admin_user)]