import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pathlib import Path
from contextlib import asynccontextmanager
from sqladmin import Admin

from src.redis_database.client import redis_manager
from src.database.session import session_manager
from src.log import setup_logger
from src.config import config
from src.auth.router import auth_router
from src.auth.template_router import auth_templates_routes
from src.admin.middleware import AdminPermissionMiddleware
from src.admin.models import UserAdmin
from src.admin.router import admin_router
from src.auth.http_handler import unauthorised_exception_handler
from src.admin.templates_router import admin_template_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекстный менеджер для управления жизненным циклом приложения.

    Алгоритм работы:
    1. Добавляем статические файлы
    2. Инициализация Redis менеджера и сохранение в app.state
    3. Инициализация менеджера сессий БД и сохранение в app.state
    4. Инициализация админки
    5. Возврат управления приложению (yield)
    6. По завершении работы:
       - Закрытие соединений Redis
       - Закрытие соединений с БД

    Args:
        app: Экземпляр FastAPI приложения
    """

    # Инициализация пулов redis
    await redis_manager.init()
    app.state.redis_manager = redis_manager

    # Инициализация сессий sql базы
    await session_manager.init()
    app.state.db_manager = session_manager

    # Инициализация админки
    admin = Admin(app, session_manager.engine)
    admin.add_view(UserAdmin)

    yield

    # Очистка
    await redis_manager.close()
    await session_manager.close()


def create_app() -> FastAPI:
    """Фабрика для создания и настройки экземпляра FastAPI.

    Алгоритм работы:
    1. Создает экземпляр FastAPI с базовыми настройками
    2. Добавляет CORS middleware
    3. Добавляет middleware для валидации токенов
    4. Подключает роутеры

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
    app.add_middleware(AdminPermissionMiddleware)
    app.add_exception_handler(HTTPException, unauthorised_exception_handler)
    app.mount('/static', StaticFiles(directory=Path(__file__).parent.parent / 'static'), name='static')
    app.include_router(auth_router)  # Установка роутера авторизации
    app.include_router(auth_templates_routes)
    app.include_router(admin_router)
    app.include_router(admin_template_router)
    return app


if __name__ == '__main__':
    """Точка входа для запуска приложения.

    Алгоритм работы:
    1. Настройка логгера
    2. Создание приложения
    3. Запуск сервера uvicorn с параметрами:
       - Хост: 0.0.0.0 (доступ с любых интерфейсов)
       - Порт: 5000
    4. Обработка возможных ошибок запуска
    """
    try:
        setup_logger()
        app = create_app()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            log_config=None,
            log_level=None,
        )

    except Exception as e:
        logger.error(f'Во время создания приложения произошла ошибка: {e}')
