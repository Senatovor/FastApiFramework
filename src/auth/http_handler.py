from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse

from src.config import config


def unauthorised_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTPException:

    1. 401: редирект на логин + удаление куки
    2. остальные: возвращает JSON с оригинальным статусом и деталями
    """
    if exc.detail == 'Срок действия токена истек':
        return RedirectResponse(url=f"{config.auth_config.REFRESH_ROUTE}?redirect_url={str(request.url)}")
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        response = RedirectResponse(config.auth_config.LOGIN_ROUTE)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    # Для всех остальных HTTPException возвращаем JSON с оригинальным статусом
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
