from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager
from datetime import datetime
from loguru import logger
from fastapi import Depends
from typing_extensions import Annotated
from redis.asyncio import Redis, ConnectionPool
from fastapi import Request

from ..config import config


class RedisClientManager:
    """Менеджер для управления подключениями к Redis.

    Предоставляет инструменты для:
    - Создания и управления пулом подключений
    - Безопасного получения клиентов Redis
    - Интеграции с FastAPI через зависимости
    - Логирования операций с Redis

    Attributes:
        redis_url (str): URL для подключения к Redis
        connection_pool (Optional[ConnectionPool]): Пул подключений Redis
    """
    def __init__(self, redis_url: str, connection_pool: ConnectionPool | None = None):
        """Инициализация менеджера подключений.

        Args:
            redis_url: URL для подключения к Redis
            connection_pool: Опциональный существующий пул подключений
        """
        self.redis_url = redis_url
        self.connection_pool: ConnectionPool | None = connection_pool

    async def init(self):
        """Инициализирует пул подключений Redis"""
        self.connection_pool = ConnectionPool.from_url(
            url=self.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis connection pool initialized")

    async def close(self):
        """Закрывает пул подключений Redis"""
        if self.connection_pool:
            await self.connection_pool.aclose()
            logger.info("Redis connection pool closed")

    @asynccontextmanager
    async def get_client(self) -> AsyncIterator[Redis]:
        """Контекстный менеджер для работы с клиентом Redis.

        Алгоритм работы:
        1. Проверяет инициализацию пула подключений
        2. Фиксирует время начала операции
        3. Получает клиента из пула подключений
        4. Возвращает клиента через yield
        5. По завершении:
           - Закрывает клиента
           - Логирует время выполнения

        Yields:
            Redis: Асинхронный клиент Redis

        Raises:
            RuntimeError: Если пул подключений не инициализирован
        """
        if not self.connection_pool:
            raise RuntimeError("Пулы redis не инициализированы")

        start_time = datetime.now()
        logger.debug("Получаю клиент redis из пулов")

        redis_client = Redis(connection_pool=self.connection_pool)
        try:
            yield redis_client
        finally:
            await redis_client.aclose()
            exec_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Клиент Redis выпущен. Время выполнения: {exec_time:.2f} сек")

    @staticmethod
    def dependency():
        async def get_session(request: Request):
            if not hasattr(request.app.state, 'redis_manager'):
                raise RuntimeError("Менеджер Redis не инициализирован в app.state")

            redis_manager = request.app.state.redis_manager

            async with redis_manager.get_client() as client:
                yield client

        return Annotated[Redis, Depends(get_session)]


redis_manager = RedisClientManager(config.redis_config.redis_url)
RedisDepends = redis_manager.dependency
