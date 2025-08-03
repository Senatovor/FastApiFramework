from fastapi import Request
from fastapi.responses import RedirectResponse
from jose import ExpiredSignatureError
from passlib.exc import InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from src.auth.handler import AuthHandler
from ..config import config


class TokenValidationMiddleware(BaseHTTPMiddleware):
    """Middleware для валидации JWT токенов.

    Обрабатывает входящие запросы и проверяет:
    - Наличие валидного access токена
    - Исключения для публичных маршрутов
    - Срок действия токена

    Attributes:
        public_routes: Список URL, которые не требуют аутентификации
    """
    async def dispatch(self, request: Request, call_next):
        """Обрабатывает входящий HTTP запрос.

        Алгоритм работы:
        1. Проверяет запросы к /login:
           - Если есть валидный токен - редирект на главную
           - Если токен невалидный - пропускает
        2. Пропускает публичные маршруты без проверки
        3. Для защищенных маршрутов:
           - Если токена нет - редирект на /login
           - Если токен истек - редирект на /refresh
           - Если токен невалидный - редирект на /login
           - При успешной проверке - добавляет user_id в request.state

        Args:
            request: Входящий HTTP запрос
            call_next: Функция для вызова следующего middleware/обработчика

        Returns:
            Response: Ответ сервера или редирект
        """

        # Пропускаем статические файлы
        if request.url.path.startswith('/static/'):
            return await call_next(request)

        # Пропускаем API-документацию
        if request.url.path in {config.DOCS_URL, config.REDOC_URL}:
            return await call_next(request)

        access_token = request.cookies.get("access_token")

        if request.url.path == config.auth_config.LOGIN_ROUTE:
            if access_token:
                try:
                    await AuthHandler.decode_jwt(access_token)
                    # Если токен валидный — редирект на главную
                    return RedirectResponse(url=config.auth_config.HOME_ROUTE)
                except (ExpiredSignatureError, InvalidTokenError):
                    # Если токен невалидный — пропускаем (остаётся на /login)
                    pass

        # Если запрос идёт на публичный маршрут — пропускаем проверку
        if request.url.path in config.auth_config.PUBLIC_ROUTES:
            return await call_next(request)

        # Если токена нет — редирект на /login
        if not access_token:
            return RedirectResponse(url=config.auth_config.LOGIN_ROUTE)

        try:
            # Проверяем токен
            payload = await AuthHandler.decode_jwt(access_token)
            request.state.user_id = payload.get("sub")
        except ExpiredSignatureError:
            # Если токен истёк — редирект на /refresh с возвратом на исходный URL
            original_url = str(request.url)
            return RedirectResponse(url=f"{config.auth_config.REFRESH_ROUTE}?redirect_url={original_url}")
        except InvalidTokenError:
            # Если токен невалидный — редирект на /login
            return RedirectResponse(url=config.auth_config.LOGIN_ROUTE)

        return await call_next(request)