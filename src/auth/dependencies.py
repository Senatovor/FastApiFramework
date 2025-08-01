import uuid
from fastapi import Depends, Request, HTTPException, status
from typing import Annotated
from jose import ExpiredSignatureError
from loguru import logger
from passlib.exc import InvalidTokenError
from redis.asyncio import Redis

from ..redis_database.client import RedisDepends
from .handler import AuthHandler
from .schemes import UserData
from ..database.session import DbSessionDepends
from .managers import UserManager


async def get_access_token_from_redis(
        user_id: uuid.UUID | str,
        session_id: str,
        redis_client: Redis,
) -> str | None:
    return await redis_client.get(f"{user_id}:{session_id}")


async def get_token_from_cookies(request: Request) -> str:
    token = request.cookies.get("Authorization")
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing")
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
        session_id = decoded_token.get("session_id")
        logger.info(session_id)
        if not await get_access_token_from_redis(
                user_id=user_id,
                session_id=session_id,
                redis_client=redis_client,
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")

        user = await manager.find_by_id(session, uuid.UUID(user_id))
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        user.session_id = session_id

        return UserData.model_validate(user)

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
