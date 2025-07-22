from fastapi.routing import APIRouter
from src.api.endpoints.users import router as user_router
from src.api.endpoints.login import router as login_router
from src.api.endpoints.related import router as related_router
from src.api.endpoints.sports import router as sports_router
from src.api.endpoints.straight import router as straight_router
from src.api.endpoints.statistic import router as statistic_router

router = APIRouter(prefix="/v1")

router.include_router(user_router)
router.include_router(login_router)
router.include_router(sports_router)
router.include_router(related_router)
router.include_router(straight_router)
router.include_router(statistic_router)
