from fastapi.routing import APIRouter
from src.api.endpoints.users import router as user_router
from src.api.endpoints.login import router as login_router
from src.api.endpoints.history import router as history_router
from src.api.endpoints.matches import router as matches_router
from src.api.endpoints.changes import router as changes_router
from src.api.endpoints.sports import router as sports_router
from src.api.endpoints.leagues import router as leagues_router

router = APIRouter(prefix="/v1")

router.include_router(user_router)
router.include_router(login_router)
router.include_router(sports_router)
router.include_router(matches_router)
router.include_router(leagues_router)
router.include_router(changes_router)
router.include_router(history_router)
