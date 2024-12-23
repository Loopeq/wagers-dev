import uuid

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication import JWTStrategy

from src.api.manager import get_user_manager
from src.data.models import User
from src.settings import settings

SECRET = settings.SECRET

cookie_transport = CookieTransport(cookie_max_age=2592000,
                                   cookie_name='wags',
                                   cookie_httponly=True,
                                   cookie_secure=True,
                                   cookie_samesite='None')


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=2592000)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user(active=True)
