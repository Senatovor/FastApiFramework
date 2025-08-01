import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager

from src.redis_database.client import redis_manager
from src.database.session import session_manager
from src.log import setup_logger
from src.config import config
from src.auth.router import auth_router
from src.users.router import users_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация
    await redis_manager.init()
    app.state.redis_manager = redis_manager

    await session_manager.init()
    app.state.db_manager = session_manager

    yield

    # Очистка
    await redis_manager.close()
    await session_manager.close()


def create_app() -> FastAPI:
    """Фабрика для создания и настройки экземпляра FastAPI приложения.

    Returns:
        FastAPI: Настроенный экземпляр FastAPI приложения
    """
    app = FastAPI(
        title=config.TITLE,
        version=config.VERSION,
        description=config.description_project,
        contact=config.contact_project,
        docs_url=config.DOCS_URL,
        redoc_url=config.REDOC_URL,
        root_path=config.ROOT_PATH,
        lifespan=lifespan
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.include_router(auth_router)     # Установка роутера авторизации
    app.include_router(users_router)
    return app

app = create_app()

if __name__ == '__main__':
    try:
        setup_logger()
        # app = create_app()
        uvicorn.run(
            'main:app',     # todo в продакшене сделать app
            host="0.0.0.0",
            port=5000,
            log_config=None,
            log_level=None,
        )
    except Exception as e:
        logger.error(f'Во время создания приложения произошла ошибка: {e}')
