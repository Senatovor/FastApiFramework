import uuid
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Annotated

from ..exceptions import ServerException
from .exceptions import AlreadyExistException, NotAuthException
from .managers import UserManager
from .schemes import RegistrateUser, UserData, LoginUser, UsernameUser
from .handler import AuthHandler


class UserService:
    """Сервис для работы с пользователями.

     Обрабатывает бизнес-логику связанную с пользователями:
    - Регистрация
    - Аутентификация
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

        Args:
            db_session: Асинхронная сессия базы данных
            register_user: Данные для регистрации

        Returns:
            str: Имя зарегистрированного пользователя

        Raises:
            AlreadyExistException: Если пользователь уже существует
            ServerException: При возникновении других ошибок
        """
        try:
            logger.info('Пользователь регистрируется...')
            register_user.password = await self.handler.get_password_hash(register_user.password)
            user = await self.manager.add(db_session, register_user)
            logger.info(f'Пользователь {user.username} зарегистрирован')
            return user.username

        except IntegrityError as e:
            if "unique constraint" in str(e.orig).lower():
                logger.error(f'Пользователь {register_user.username} уже существует')
                raise AlreadyExistException
            logger.error(f'Ошибка - IntegrityError: {e}')
            raise ServerException

    async def login(
            self,
            db_session: AsyncSession,
            login_user: LoginUser,
            redis_client: Redis
    ) -> str:
        """Аутентифицирует пользователя в системе.

        Args:
            db_session: Асинхронная сессия базы данных
            login_user: Данные для входа
            redis_client: Клиент Redis для хранения сессий

        Returns:
            str: JWT токен аутентификации

        Raises:
            NotAuthException: Если аутентификация не удалась
            ServerException: При возникновении других ошибок
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
                raise NotAuthException
            session_id: str = str(uuid.uuid4())
            token = await self.handler.create_token(
                data={
                    "sub": str(user.id),
                    'session_id': session_id,
                },
            )
            await redis_client.set(f"{user.id}:{session_id}", token)
            return token

        except Exception as server_error:
            logger.error(f'Во время авторизации произошла ошибка: {server_error}')
            raise ServerException

    @staticmethod
    async def logout_user(
            user: UserData,
            redis_client: Redis
    ):
        """Завершает сессию пользователя.

        Args:
            user: Данные пользователя
            redis_client: Клиент Redis для удаления сессии

        Raises:
            ServerException: При возникновении ошибок
        """
        try:
            await redis_client.delete(f"{user.id}:{user.session_id}")
        except Exception as server_error:
            logger.error(f'Во время выхода произошла ошибка: {server_error}')
            raise ServerException
