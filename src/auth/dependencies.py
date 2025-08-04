import uuid
from fastapi import Depends, Request
from typing import Annotated
from jose import ExpiredSignatureError
from loguru import logger
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


async def get_session_from_redis(
        user_id: uuid.UUID | str,
        redis_client: Redis,
) -> str | None:
    """Получает сессию пользователя из Redis.

    Args:
        user_id: Идентификатор пользователя
        redis_client: Клиент Redis

    Returns:
        str | None: Идентификатор сессии или None если не найдено
    """
    return await redis_client.get(f"session:{user_id}")


async def get_token_from_cookies(request: Request) -> str:
    """Извлекает access token из cookies запроса.

    Args:
        request: Объект запроса FastAPI

    Returns:
        str: Access token

    Raises:
        HttpTokenMissingException: Если токен отсутствует в cookies
    """
    token = request.cookies.get("access_token")
    if token is None:
        raise HttpTokenMissingException
    return token


async def have_tokens_in_cookies(request: Request) -> bool:
    """Проверяет наличие токенов в cookies.

    Args:
        request: Объект запроса FastAPI

    Returns:
        bool: True если оба токена присутствуют, иначе False
    """
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    if (access_token and refresh_token) is None:
        return False
    return True


async def get_current_user(
        request: Request,
        session: DbSessionDepends(),
        redis_client: RedisDepends(),
        token: Annotated[str, Depends(get_token_from_cookies)],
        handler: AuthHandler = Depends(AuthHandler),
        manager: UserManager = Depends(UserManager),
) -> UserData:
    """Зависимость для получения данных текущего аутентифицированного пользователя.

    Алгоритм работы:
    1. Декодирует JWT токен
    2. Проверяет наличие активной сессии в Redis
    3. Ищет пользователя в базе данных
    4. Возвращает данные пользователя

    Args:
        request: Объект запроса FastAPI
        session: Сессия базы данных
        redis_client: Клиент Redis
        token: Access token из cookies
        handler: Обработчик аутентификации
        manager: Менеджер пользователей

    Returns:
        UserData: Данные аутентифицированного пользователя

    Raises:
        HttpTokenIsInvalidException: Невалидный токен или сессия
        HttpUserNotFoundException: Пользователь не найден
        HttpExpiredSignatureException: Истек срок действия токена
    """
    try:
        decoded_token = await handler.decode_jwt(token)
        user_id = decoded_token.get("sub")
        if not await get_session_from_redis(
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
