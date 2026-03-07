from src.api.endpoints import router as v1_router
from src.core.setup import create_application

app = create_application(router=v1_router)
