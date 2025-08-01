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
    """
    Полноценный менеджер для работы с Redis в FastAPI
    с корректным доступом из зависимостей.
    """
    def __init__(self, redis_url: str, connection_pool: ConnectionPool | None = None):
        self.redis_url = redis_url
        self.connection_pool: ConnectionPool | None = connection_pool

    async def init(self):
        """Инициализация пула подключений при старте приложения"""
        self.connection_pool = ConnectionPool.from_url(
            url=self.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis connection pool initialized")

    async def close(self):
        """Очистка ресурсов при завершении работы"""
        if self.connection_pool:
            await self.connection_pool.aclose()
            logger.info("Redis connection pool closed")

    @asynccontextmanager
    async def get_client(self) -> AsyncIterator[Redis]:
        """Основной контекстный менеджер для работы с Redis"""
        if not self.connection_pool:
            raise RuntimeError("Redis connection pool is not initialized")

        start_time = datetime.now()
        logger.debug("Acquiring Redis client from pool")

        redis_client = Redis(connection_pool=self.connection_pool)
        try:
            yield redis_client
        finally:
            await redis_client.aclose()
            exec_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Redis client released. Execution time: {exec_time:.2f} sec")

    @staticmethod
    def dependency():
        async def get_session(request: Request):
            if not hasattr(request.app.state, 'redis_manager'):
                raise RuntimeError("Database manager not initialized in app.state")

            redis_manager = request.app.state.redis_manager

            async with redis_manager.get_client() as client:
                yield client

        return Annotated[Redis, Depends(get_session)]


redis_manager = RedisClientManager(config.redis_config.redis_url)
RedisDepends = redis_manager.dependency
