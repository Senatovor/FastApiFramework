import uuid
from fastapi import Depends, Request
from typing import Annotated
from jose import ExpiredSignatureError
from passlib.exc import InvalidTokenError
from redis.asyncio import Redis

from .exceptions import (
    HttpTokenIsInvalidException,
    HttpUserNotFoundException,
    HttpExpiredSignatureException,
    HttpTokenMissingException
)
from ..redis_database.client import RedisDepends
from .handler import AuthHandler
from .schemes import UserData
from ..database.session import DbSessionDepends
from .managers import UserManager


async def get_access_token_from_redis(
        user_id: uuid.UUID | str,
        redis_client: Redis,
) -> str | None:
    return await redis_client.get(f"session:{user_id}")


async def get_token_from_cookies(request: Request) -> str:
    token = request.cookies.get("access_token")
    if token is None:
        raise HttpTokenMissingException
    return token


async def get_current_user(
        session: DbSessionDepends(),
        redis_client: RedisDepends(),
        token: Annotated[str, Depends(get_token_from_cookies)],
        handler: AuthHandler = Depends(AuthHandler),
        manager: UserManager = Depends(UserManager),
) -> UserData:
    try:
        decoded_token = await handler.decode_jwt(token)
        user_id = decoded_token.get("sub")
        if not await get_access_token_from_redis(
                user_id=user_id,
                redis_client=redis_client,
        ):
            raise HttpTokenIsInvalidException

        user = await manager.find_by_id(session, uuid.UUID(user_id))
        if user is None:
            raise HttpUserNotFoundException

        return UserData.model_validate(user)

    except ExpiredSignatureError:
        raise HttpExpiredSignatureException
    except InvalidTokenError:
        raise HttpTokenIsInvalidException
