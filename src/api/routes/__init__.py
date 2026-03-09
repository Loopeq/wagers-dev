from fastapi.routing import APIRouter
from src.api.endpoints.admin import router as admin_router
from src.api.endpoints.market import router as market_router
from src.api.endpoints.user import router as user_router

router = APIRouter(prefix="/v1")

router.include_router(admin_router)
router.include_router(user_router)
router.include_router(market_router)
