from fastapi import status
from fastapi.exceptions import HTTPException


class BaseAppException(Exception):
    """Базовый класс для пользовательских исключений приложения.

    Attributes:
        details: Описание ошибки
        headers: Дополнительные HTTP заголовки
        status_code: HTTP статус код ошибки
    """
    details: str | None = None
    headers: dict[str, str] | None = None
    status_code: int | None = None

    def __init__(self):
        super().__init__(self.details)

    def to_http_exception(self) -> HTTPException:
        """Конвертирует исключение в HTTPException для обработки в FastAPI.

        Returns:
            HTTPException: Исключение, готовое для обработки FastAPI
        """
        return HTTPException(
            status_code=self.status_code,
            detail=self.details,
            headers=self.headers
        )


class ServerException(BaseAppException):
    """Исключение для ошибок сервера"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    details = 'Ошибка сервера'

