from fastapi.routing import APIRouter
from src.api.endpoints.users import router as user_router
from src.api.endpoints.login import router as login_router
from src.api.endpoints.registration import router as registration_router
from src.api.endpoints.statistic import router as statistic_router
from src.api.endpoints.admin import router as admin_router
from src.api.endpoints.logout import router as logout_router
from src.api.endpoints.market import router as market_router
router = APIRouter(prefix="/v1")

router.include_router(admin_router)
router.include_router(user_router)
router.include_router(logout_router)
router.include_router(login_router)
router.include_router(registration_router)
router.include_router(statistic_router)
router.include_router(market_router)