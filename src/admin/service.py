"""Сервисный слой для администрирования пользовательских сессий.

Содержит бизнес-логику для:
- Получения списка активных сессий
- Управления сессиями (удаление)
"""

from typing import Annotated, Dict
from fastapi import Depends
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.auth.handler import AuthHandler
from src.auth.managers import UserManager
from src.exceptions import HttpServerException


class AdminService:
    """Сервис для административных операций с сессиями пользователей.

    Attributes:
        manager: Менеджер для работы с пользователями в БД
        handler: Обработчик аутентификации
    """

    def __init__(
            self,
            manager: Annotated[UserManager, Depends(UserManager)],
            handler: Annotated[AuthHandler, Depends(AuthHandler)],
    ) -> None:
        self.manager = manager
        self.handler = handler

    async def get_all_sessions(
            self,
            redis_client: Redis,
            db_session: AsyncSession
    ) -> Dict[str, str]:
        """Получает все активные сессии пользователей.

        Алгоритм работы:
        1. Итерируется по ключам Redis с шаблоном 'session:*'
        2. Для каждого ключа получает user_id
        3. Находит пользователя в БД по user_id
        4. Формирует словарь {username: user_id}

        Args:
            redis_client: Клиент Redis
            db_session: Сессия базы данных

        Returns:
            Dict[str, str]: Словарь {имя_пользователя: id_сессии}

        Raises:
            HttpServerException: При ошибках доступа к Redis или БД
        """
        try:
            sessions = {}
            cursor = 0
            pattern = "session:*"

            while True:
                cursor, keys = await redis_client.scan(cursor, match=pattern, count=1000)
                for key in keys:
                    user_id = await redis_client.get(key)
                    if not user_id:
                        continue

                    try:
                        user = await self.manager.find_by_id(db_session, uuid.UUID(user_id))
                        if user:
                            sessions[user.username] = user_id
                    except Exception as e:
                        logger.warning(f"Ошибка поиска пользователя {user_id}: {e}")
                        continue

                if cursor == 0:
                    break

            return sessions
        except Exception as e:
            logger.error(f'Ошибка получения сессий: {e}')
            raise HttpServerException

    @staticmethod
    async def delete_user_session(
            redis_client: Redis,
            session_id: str
    ) -> None:
        """Удаляет конкретную пользовательскую сессию.

        Args:
            redis_client: Клиент Redis
            session_id: Идентификатор сессии для удаления

        Notes:
            Не выбрасывает исключение если сессия не найдена
        """
        key = f"session:{session_id}"
        deleted = await redis_client.delete(key)
        if deleted:
            logger.info(f"Сессия {session_id} удалена")
        else:
            logger.warning(f"Сессия {session_id} не найдена")

    async def delete_all_user_session(
            self,
            redis_client: Redis,
            db_session: AsyncSession
    ) -> None:
        """Удаляет все активные пользовательские сессии.

        Args:
            redis_client: Клиент Redis
            db_session: Сессия базы данных

        Raises:
            HttpServerException: При ошибках доступа к Redis
        """
        try:
            sessions = await self.get_all_sessions(redis_client, db_session)
            for user_id in sessions.values():
                key = f"session:{user_id}"
                await redis_client.delete(key)
            logger.info(f"Удалено {len(sessions)} сессий")
        except Exception as e:
            logger.error(f'Ошибка удаления сессий: {e}')
            raise HttpServerException