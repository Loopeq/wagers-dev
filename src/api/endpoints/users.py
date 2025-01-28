from fastapi.routing import APIRouter
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.schemas import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_user_me(current_user: CURRENT_ACTIVE_USER):
    return current_user
