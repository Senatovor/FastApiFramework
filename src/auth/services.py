from fastapi import Depends
from passlib.exc import InvalidTokenError
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Annotated

from ..config import config
from ..exceptions import HttpServerException
from .exceptions import (
    HttpAlreadyExistException,
    HttpNotAuthException,
    HttpInvalidTokenTypeException,
    HttpTokenIsInvalidException
)
from .managers import UserManager
from .schemes import RegistrateUser, UserData, LoginUser, UsernameUser
from .handler import AuthHandler


class UserService:
    """Сервис для работы с пользователями.

    Обрабатывает бизнес-логику связанную с пользователями:
    - Регистрация
    - Аутентификация
    - Обновление токенов
    - Выход из системы

    Attributes:
        manager: Менеджер для работы с базой данных
        handler: Обработчик аутентификации
    """

    def __init__(
            self,
            manager: Annotated[UserManager, Depends(UserManager)],
            handler: Annotated[AuthHandler, Depends(AuthHandler)],
    ) -> None:
        self.manager = manager
        self.handler = handler

    async def register(
            self,
            db_session: AsyncSession,
            register_user: RegistrateUser,
    ) -> str:
        """Регистрирует нового пользователя в системе.

        - Получает данные для регистрации
        - Хеширует пароль
        - Сохраняет пользователя в БД
        - Обрабатывает возможные конфликты уникальности

        Args:
            db_session: Асинхронная сессия базы данных
            register_user: Данные для регистрации

        Returns:
            str: Имя зарегистрированного пользователя

        Raises:
            HttpAlreadyExistException: Если пользователь уже существует
            HttpServerException: При возникновении других ошибок
        """
        try:
            logger.info(f'Пользователь {register_user.username} регистрируется...')
            register_user.password = await self.handler.get_password_hash(register_user.password)
            user = await self.manager.add(db_session, register_user)
            logger.info(f'Пользователь {user.username} зарегистрирован')
            return user.username

        except IntegrityError as e:
            if "unique constraint" in str(e.orig).lower():
                logger.error(f'Пользователь {register_user.username} уже существует')
                raise HttpAlreadyExistException
            logger.error(f'Ошибка - IntegrityError: {e}')
            raise HttpServerException

    async def login(
            self,
            db_session: AsyncSession,
            login_user: LoginUser,
            redis_client: Redis
    ) -> tuple[str, str]:
        """Аутентифицирует пользователя в системе.

        - Проверяет существование пользователя
        - Верифицирует пароль
        - Генерирует пару токенов (access и refresh)
        - Сохраняет сессию в Redis
        - Возвращает токены

        Args:
            db_session: Асинхронная сессия базы данных
            login_user: Данные для входа
            redis_client: Клиент Redis для хранения сессий

        Returns:
            tuple[str, str]: JWT токены аутентификации

        Raises:
            HttpNotAuthException: Если аутентификация не удалась
            HttpServerException: При возникновении других ошибок
        """
        try:
            user = await self.manager.find_one_by(
                db_session,
                UsernameUser(username=login_user.username)
            )
            if user is None or not await self.handler.verify_password(
                    plain_password=login_user.password.get_secret_value(),
                    hashed_password=user.password
            ):
                raise HttpNotAuthException

            access_token = await self.handler.create_token(
                data={
                    "sub": str(user.id),
                },
                timedelta_minutes=config.auth_config.ACCESS_TOKEN_EXPIRE,
                token_type='access'
            )
            refresh_token = await self.handler.create_token(
                data={
                    "sub": str(user.id),
                },
                timedelta_minutes=config.auth_config.REFRESH_TOKEN_EXPIRE,
                token_type='refresh'
            )

            await redis_client.set(
                f"session:{str(user.id)}",
                str(user.id),
            )

            return access_token, refresh_token

        except Exception as server_error:
            logger.error(f'Во время авторизации произошла ошибка: {server_error}')
            raise HttpServerException

    async def refresh_token(
            self,
            refresh_token: str,
            redis_client: Redis
    ) -> tuple[str, str]:
        """Обновляет access token с помощью refresh token.

        - Проверяет валидность refresh токена
        - Проверяет соответствие сессии в Redis
        - Генерирует новую пару токенов
        - Возвращает обновленные токены

        Args:
            refresh_token: Refresh токен для обновления
            redis_client: Клиент Redis для проверки сессии

        Returns:
            tuple[str, str]: Новая пара токенов (access, refresh)

        Raises:
            HttpInvalidTokenTypeException: Если передан не refresh токен
            HttpTokenIsInvalidException: Если токен или сессия невалидны
        """
        try:
            payload = await self.handler.decode_jwt(refresh_token)
            if payload.get("type") != "refresh":
                raise HttpInvalidTokenTypeException

            user_id = payload.get("sub")

            session_id = await redis_client.get(f"session:{user_id}")
            if session_id != user_id:
                raise HttpTokenIsInvalidException

            new_access_token = await self.handler.create_token(
                data={
                    "sub": user_id,
                },
                timedelta_minutes=config.auth_config.ACCESS_TOKEN_EXPIRE,
                token_type='access'
            )
            new_refresh_token = await self.handler.create_token(
                data={
                    "sub": user_id,
                },
                timedelta_minutes=config.auth_config.REFRESH_TOKEN_EXPIRE,
                token_type='refresh'
            )

            return new_access_token, new_refresh_token

        except InvalidTokenError:
            raise HttpTokenIsInvalidException

    @staticmethod
    async def logout_user(
            user: UserData,
            redis_client: Redis
    ):
        """Завершает сессию пользователя.

        - Удаляет сессию пользователя из Redis
        - Инвалидирует токены

        Args:
            user: Данные пользователя
            redis_client: Клиент Redis для удаления сессии

        Raises:
            ServerException: При возникновении ошибок
        """
        try:
            await redis_client.delete(f"session:{user.id}")
        except Exception as server_error:
            logger.error(f'Во время выхода произошла ошибка: {server_error}')
            raise HttpServerException
