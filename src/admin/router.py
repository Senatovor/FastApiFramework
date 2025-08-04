from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from .service import AdminService
from ..database.session import DbSessionDepends
from ..exceptions import HttpServerException
from ..redis_database.client import RedisDepends
from ..utils import ok_response_docs, error_response_docs

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@admin_router.post(
    '/get_sessions',
    name='get_sessions',
    summary='Выдает все сессии',
    status_code=status.HTTP_200_OK,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Передача сессий прошла успешно'
        ),
        **error_response_docs(
            HttpServerException
        )
    }
)
async def get_sessions(
        redis_client: RedisDepends(),
        db_session: DbSessionDepends(),
        service: AdminService = Depends(AdminService),
) -> dict:
    """Получает все активные пользовательские сессии.

    Args:
        redis_client: Клиент Redis для доступа к сессиям
        db_session: Сессия базы данных
        service: Сервис для работы с админ-функциями

    Returns:
        dict: Словарь с активными сессиями

    Raises:
        HttpServerException: При возникновении ошибок сервера
    """
    redis_session = await service.get_all_sessions(redis_client, db_session)
    return redis_session


@admin_router.post(
    '/sessions_management/delete/{session_id}',
    name='sessions_delete',
    summary='Удаляет сессию',
    status_code=status.HTTP_200_OK,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Передача сессий прошла успешно'
        ),
        **error_response_docs(
            HttpServerException
        )
    }
)
async def sessions_delete(
        session_id: str,
        redis_client: RedisDepends(),
        service: AdminService = Depends(AdminService),
):
    """Удаляет конкретную пользовательскую сессию.

    Args:
        session_id: Идентификатор сессии для удаления
        redis_client: Клиент Redis
        service: Сервис для работы с админ-функциями

    Returns:
        JSONResponse: Сообщение об успешном удалении

    Raises:
        HttpServerException: При возникновении ошибок сервера
    """
    await service.delete_user_session(redis_client, session_id)
    return JSONResponse(content={'message': 'Удаление прошло успешно'})


@admin_router.post(
    '/sessions_management/delete_all',
    name='sessions_delete_all',
    status_code=status.HTTP_200_OK,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Удаляет все сессии'
        ),
        **error_response_docs(
            HttpServerException
        )
    }
)
async def sessions_delete(
        redis_client: RedisDepends(),
        db_session: DbSessionDepends(),
        service: AdminService = Depends(AdminService),
):
    """Удаляет все активные пользовательские сессии.

    Args:
        redis_client: Клиент Redis
        db_session: Сессия базы данных
        service: Сервис для работы с админ-функциями

    Returns:
        JSONResponse: Сообщение об успешном удалении

    Raises:
        HttpServerException: При возникновении ошибок сервера
    """
    await service.delete_all_user_session(redis_client, db_session)
    return JSONResponse(content={'message': 'Удаление прошло успешно'})
