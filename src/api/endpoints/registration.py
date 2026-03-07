from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db.db_helper import db_helper
from src.core.schemas import RegisterForm
from src.core.crud.api.invite import InviteCodeOrm
from src.core.crud.api.user import UserOrm
from src.core.utils import get_password_hash
from src.core.schemas import UserOut

router = APIRouter(prefix="/registration", tags=["Registration"])


@router.post("", response_model=UserOut)
async def login_for_access_token(
    form_data: RegisterForm,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    invite = await InviteCodeOrm.get_by_code(form_data.invite_code, session)
    if not invite or invite.is_used:
        raise HTTPException(status_code=400, detail="Invalid invite code")

    existing_user = await UserOrm.get_user_by_email(form_data.email, session)
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    user = await UserOrm.create_user(
        email=form_data.email,
        password=get_password_hash(form_data.password),
        session=session,
    )

    await InviteCodeOrm.mark_used(invite, user.email, session)

    return user
