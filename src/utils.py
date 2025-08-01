from fastapi import status
from typing import Type

from src.schemes import DetailResponse


def ok_response_docs(
        description: str | None = None,
        status_code: int = status.HTTP_200_OK,
) -> dict:
    """Генерирует документацию для положительных ответов в формате OpenAPI.

    Args:
        status_code: Статус ответа
        description: Описание ошибки для документации

    Returns:
        Словарь с описанием ошибки в формате OpenAPI
    """
    return {
        status_code: {
            "model": DetailResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": {"detail": description}
                }
            }
        }
    }


def error_response_docs(
        status_code: int,
        error: Type[Exception],
) -> dict:
    """Генерирует документацию для ошибок в формате OpenAPI.

    Args:
        status_code: HTTP статус код
        error: Класс исключения

    Returns:
        Словарь с описанием ошибки в формате OpenAPI
    """
    error_instance = error()

    return {
        status_code: {
            "model": DetailResponse,
            "description": str(error_instance),
            "content": {
                "application/json": {
                    "example": {"detail": str(error_instance)}
                }
            }
        }
    }
