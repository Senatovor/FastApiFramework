from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, AsyncEngine
from functools import wraps
from fastapi import Depends
from typing import Annotated, AsyncIterator, Optional
from loguru import logger
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import Request

from ..config import config

SQL_DATABASE_URL = config.database_config.database_url


class DatabaseSessionManager:
    """Менеджер для управления асинхронными сессиями базы данных.

     Предоставляет инструменты для:
    - Создания и управления сессиями БД
    - Контроля транзакций с настраиваемым уровнем изоляции
    - Интеграции с FastAPI через зависимости
    - Логирования операций с БД

    Attributes:
        database_url (str): URL для подключения к БД
        engine (Optional[AsyncEngine]): Асинхронный движок SQLAlchemy
        session_factory (Optional[async_sessionmaker[AsyncSession]]): Фабрика для создания сессий
    """

    def __init__(
            self,
            database_url: str,
            session_factory: async_sessionmaker[AsyncSession] | None = None,
            engine: AsyncEngine | None = None
    ) -> None:
        """Инициализация менеджера сессий.

        Args:
            database_url: URL для подключения к БД
            session_factory: Опциональная фабрика сессий
            engine: Опциональный существующий движок
        """
        self.database_url = database_url
        self.engine = engine
        self.session_factory = session_factory

    async def init(self):
        """Инициализирует движок базы данных и фабрику сессий."""
        self.engine = create_async_engine(
            url=self.database_url,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False
        )
        logger.success("Движок базы данных инициализировано")

    async def close(self):
        """Закрывает соединения с базой данных."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine closed")

    @asynccontextmanager
    async def session(
            self,
            isolation_level: str | None = None,
            commit: bool = False
    ) -> AsyncIterator[AsyncSession]:
        """Контекстный менеджер для сессий базы данных.

         Алгоритм работы:
        1. Фиксирует время начала операции
        2. Создает новую сессию через session_factory
        3. Если указан isolation_level - устанавливает его для транзакции
        4. Возвращает сессию через yield (точка входа в контекст)
        5. При выходе из контекста:
           - Если commit=True -> выполняет commit
           - В случае ошибки -> выполняет rollback
           - В любом случае закрывает сессию
        6. Логирует время выполнения операции

        Args:
            isolation_level: Уровень изоляции транзакции (None, 'READ COMMITTED' и т.д.)
            commit: Флаг автоматического коммита изменений

        Yields:
            AsyncSession: Асинхронная сессия базы данных

        Raises:
            Exception: Любые ошибки при работе с БД
        """
        start_time = datetime.now()
        logger.info(f"Создание новой сессии. Изоляция: {isolation_level}, Автокоммит: {commit}")
        async with self.session_factory() as session:
            try:
                if isolation_level:
                    logger.debug(f"Установка уровня изоляции: {isolation_level}")
                    await session.execute(
                        text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
                    )

                yield session

                if commit:
                    logger.debug("Выполнение коммита изменений")
                    await session.commit()
                    logger.info("Изменения успешно закоммичены")
            except Exception as e:
                logger.error(f"Ошибка в сессии: {str(e)}", exc_info=True)
                await session.rollback()
                logger.info("Выполнен откат транзакции")
                raise
            finally:
                await session.close()
                exec_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Сессия закрыта. Время выполнения: {exec_time:.2f} сек")

    @staticmethod
    def dependency(isolation_level: str | None = None, commit: bool = False):
        """Создает зависимость FastAPI для работы с сессиями.

         Алгоритм работы:
        1. Создает асинхронную функцию-зависимость get_session
        2. Проверяет инициализацию менеджера в app.state
        3. Использует session() как контекстный менеджер
        4. Возвращает зависимость FastAPI для внедрения сессии

        Args:
            isolation_level: Уровень изоляции транзакции
            commit: Флаг автоматического коммита

        Returns:
            Annotated[AsyncSession, Depends]: Зависимость для внедрения сессии

        Raises:
            RuntimeError: Если менеджер не инициализирован в app.state
        """
        async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
            if not hasattr(request.app.state, 'db_manager'):
                raise RuntimeError("Database manager not initialized in app.state")

            db_manager: DatabaseSessionManager = request.app.state.db_manager

            async with db_manager.session(isolation_level, commit) as session:
                yield session

        return Annotated[AsyncSession, Depends(get_session)]

    def connection(self, isolation_level: str | None = None, commit: bool = False):
        """
        Декоратор для управления транзакциями в функциях.

        1. Создает новую сессию с указанным уровнем изоляции
        2. Передает сессию в декорируемую функцию
        3. Обрабатывает коммит/откат транзакции
        4. Гарантирует закрытие сессии

        Args:
            isolation_level: Уровень изоляции транзакции
            commit: Автоматически коммитить изменения

        Returns:
            Декоратор для функций, работающих с БД
        """

        def decorator(method):
            @wraps(method)
            async def wrapper(*args, **kwargs):
                start_time = datetime.now()
                logger.info(f"Начало транзакции для {method.__name__}. Изоляция: {isolation_level}")
                async with self.session_factory() as session:
                    try:
                        if isolation_level:
                            logger.debug(f"Установка уровня изоляции: {isolation_level}")
                            await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
                        logger.debug(f"Выполнение метода {method.__name__}")
                        result = await method(*args, session=session, **kwargs)
                        if commit:
                            logger.debug("Выполнение коммита изменений")
                            await session.commit()
                            logger.info("Изменения успешно закоммичены")
                        return result
                    except Exception as e:
                        logger.error(f"Ошибка в транзакции {method.__name__}: {str(e)}", exc_info=True)
                        await session.rollback()
                        logger.info("Выполнен откат транзакции")
                        raise
                    finally:
                        await session.close()
                        exec_time = (datetime.now() - start_time).total_seconds()
                        logger.info(f"Транзакция завершена. Время выполнения: {exec_time:.2f} сек")

            return wrapper

        return decorator


# Глобальный экземпляр менеджера сессий
session_manager = DatabaseSessionManager(SQL_DATABASE_URL)
# Или вы можете инициализировать его так, для использования вне FastAPI:
#
# engine = create_async_engine(SQL_DATABASE_URL, future=True)
# session_manager = DatabaseSessionManager(
#     database_url=SQL_DATABASE_URL,
#     engine=engine,
#     session_factory=async_sessionmaker(engine, expire_on_commit=False)
# )

# Стандартная зависимость для FastAPI
DbSessionDepends = session_manager.dependency

# Пример использования зависимости для FastAPI
#
# @app.get("/")
# async def test(session: DbSessionDepends(commit=True)):
#     session.add(User(name='Пеня', gender='MALE'))
#     return {"message": "User created"}
