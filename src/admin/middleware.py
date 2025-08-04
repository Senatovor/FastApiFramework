from fastapi import Request, status
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from typing import Callable

from jose import ExpiredSignatureError
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from ..auth.handler import AuthHandler
from ..auth.managers import UserManager
from ..config import config


class AdminPermissionMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки прав администратора.

    Алгоритм работы:
    1. Пропускает все запросы не к /admin маршрутам
    2. Для /admin маршрутов:
       a. Извлекает access_token из cookies
       b. Декодирует токен и получает user_id
       c. Проверяет активную сессию в Redis
       d. Ищет пользователя в базе данных
       e. Проверяет флаг is_superuser
       f. Если проверки пройдены - пропускает запрос
       g. Если нет - возвращает соответствующую ошибку
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Обрабатывает HTTP запрос и проверяет права администратора.

        Args:
            request: Входящий HTTP запрос
            call_next: Функция для вызова следующего middleware/обработчика

        Returns:
            Response: Ответ сервера или JSON с ошибкой доступа

        Примеры ошибок:
            - 401: Проблемы с аутентификацией
            - 403: Нет прав администратора
            - 404: Пользователь не найден
        """
        # Шаг 1: Пропускаем запросы не к /admin
        if not request.url.path.startswith("/admin"):
            return await call_next(request)

        try:
            # Шаг 2a: Получаем токен из cookies
            token = request.cookies.get("access_token")
            if not token:
                raise Exception('Нету токена')

            # Шаг 2b: Декодируем токен
            decoded_token = await AuthHandler.decode_jwt(token)
            user_id = decoded_token.get("sub")
            if not user_id:
                raise Exception('Токен не действителен')

            # Шаг 2c: Проверяем сессию в Redis
            redis_manager = request.app.state.redis_manager
            async with redis_manager.get_client() as client:
                if not await client.get(f"session:{user_id}"):
                    raise Exception('Вашей сессии нету в базе')

            # Шаг 2d: Ищем пользователя в БД
            database_manager = request.app.state.db_manager
            async with database_manager.session() as session:
                user = await UserManager.find_by_id(session, user_id)
                if user is None:
                    raise Exception('Нету такого пользователя')

                # Шаг 2e: Проверяем права администратора
                if not user.is_superuser:
                    logger.warning(f"Попытка доступа в админ-зону без прав: {request.url}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Доступ запрещен. Требуются права администратора"}
                    )

            # Шаг 2f: Все проверки пройдены
            return await call_next(request)

        except ExpiredSignatureError:
            return RedirectResponse(url=f'{config.auth_config.REFRESH_ROUTE}?redirect_url={str(request.url)}')
        except Exception as e:
            # Обработка непредвиденных ошибок
            logger.error(f"Ошибка проверки прав администратора: {str(e)}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Ошибка авторизации: {str(e)}"}
            )
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response
