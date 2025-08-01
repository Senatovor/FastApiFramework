from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from loguru import logger
from redis.asyncio import Redis
from typing import Annotated

from ..exceptions import ServerException
from ..database.session import DbSessionDepends
from ..redis_database.client import RedisDepends
from ..utils import error_response_docs, ok_response_docs
from .dependencies import get_current_user
from .services import UserService
from .schemes import RegistrateUser, UserData, LoginUser
from .exceptions import NotAuthException, AlreadyExistException

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)


@auth_router.post(
    '/register',
    name='register',
    summary="Регистрация пользователя",
    description=
    """
    Создание нового пользователя в системе.
    Требует уникального username и email.
    Пароль хранится в зашифрованном виде.
    """,
    status_code=status.HTTP_201_CREATED,
    response_class=JSONResponse,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_201_CREATED,
            description='Пользователь успешно создан'
        ),
        **error_response_docs(
            status_code=status.HTTP_409_CONFLICT,
            error=AlreadyExistException
        ),
        **error_response_docs(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=ServerException
        )
    }
)
async def register(
        register_user: RegistrateUser,
        db_session: DbSessionDepends(commit=True),
        service: Annotated[UserService, Depends(UserService)],
):
    """Регистрирует нового пользователя.

    Args:
        register_user: Данные для регистрации
        db_session: Сессия базы данных
        service: Сервис для работы с пользователями

    Returns:
        JSONResponse: Сообщение об успешной регистрации

    Raises:
        HTTPException: 409 если пользователь уже существует
        HTTPException: 500 при внутренней ошибке сервера
    """
    try:
        username = await service.register(db_session, register_user)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": f'Пользователь {username} создан'}
        )
    except AlreadyExistException as e:
        raise e.to_http_exception()
    except ServerException as e:
        raise e.to_http_exception()


@auth_router.post(
    '/login',
    name='login',
    summary="Вход в систему",
    description=
    """
    Аутентификация по логину и паролю.
    При успешном входе устанавливается cookie с JWT токеном.
    """,
    status_code=status.HTTP_200_OK,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Успешная авторизация'
        ),
        **error_response_docs(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error=NotAuthException
        ),
        **error_response_docs(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=ServerException
        )
    }
)
async def login(
        login_user: LoginUser,
        session: DbSessionDepends(),
        redis_client: RedisDepends(),
        service: Annotated[UserService, Depends(UserService)],
):
    """Аутентифицирует пользователя в системе.

    Args:
        login_user: Данные для входа (username и password)
        session: Сессия базы данных
        service: Сервис для работы с пользователями
        redis_client: Клиент Redis для хранения сессий

    Returns:
        JSONResponse: Сообщение об успешном входе и cookie с токеном

    Raises:
        HTTPException: 401 при неверных учетных данных
        HTTPException: 500 при внутренней ошибке сервера
    """
    try:
        token = await service.login(session, login_user, redis_client)
        logger.info(token)
        response = JSONResponse(content={"message": "Вход успешен"})
        response.set_cookie(
            key="Authorization",
            value=token,
            httponly=True,
        )
        return response
    except NotAuthException as e:
        raise e.to_http_exception()
    except ServerException as e:
        raise e.to_http_exception()


@auth_router.get(
    path="/logout",
    name='logout',
    summary="Выход из системы",
    description=
    """
    Завершает текущую сессию пользователя.
    Удаляет JWT токен из cookies.
    """,
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Удачный выход'
        ),
    }
)
async def logout(
        user: Annotated[UserData, Depends(get_current_user)],
        service: Annotated[UserService, Depends(UserService)],
        redis_client: RedisDepends(),
):
    """Завершает сессию пользователя.

    Args:
        user: Данные текущего пользователя
        service: Сервис для работы с пользователями
        redis_client: Клиент Redis для удаления сессии

    Returns:
        JSONResponse: Сообщение об успешном выходе

    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    try:
        await service.logout_user(user, redis_client)
        response = JSONResponse(content={"message": "Вы успешно вышли из системы"})
        response.delete_cookie(key="Authorization")

        return response
    except ServerException as e:
        raise e.to_http_exception()
