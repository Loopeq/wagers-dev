from fastapi.routing import APIRouter
from src.api.endpoints.users import router as user_router
from src.api.endpoints.login import router as login_router

router = APIRouter(prefix="/v1")

router.include_router(user_router)
router.include_router(login_router)
