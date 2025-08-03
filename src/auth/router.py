from fastapi import APIRouter, Depends, status, Request, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from typing import Annotated

from ..config import templates
from ..exceptions import HttpServerException
from ..database.session import DbSessionDepends
from ..redis_database.client import RedisDepends
from ..utils import error_response_docs, ok_response_docs
from .dependencies import get_current_user
from .services import UserService
from .schemes import RegistrateUser, UserData, LoginUser
from .exceptions import (
    HttpNotAuthException,
    HttpAlreadyExistException,
    HttpInvalidTokenTypeException,
    HttpTokenIsInvalidException,
)

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
            error=HttpAlreadyExistException
        ),
        **error_response_docs(
            error=HttpServerException
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
    username = await service.register(db_session, register_user)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": f'Пользователь {username} создан'}
    )

@auth_router.post(
    '/login',
    name='login',
    summary="Вход в систему",
    description=
    """
    Аутентификация по логину и паролю.
    """,
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Удачная авторизация'
        ),
        **error_response_docs(
            HttpNotAuthException
        ),
        **error_response_docs(
            HttpServerException
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
        redis_client: Клиент Redis для хранения сессий
        service: Сервис для работы с пользователями

    Returns:
        JSONResponse: Сообщение об успешном входе и cookie с токеном

    Raises:
        HTTPException: 401 при неверных учетных данных
        HTTPException: 500 при внутренней ошибке сервера
    """
    access_token, refresh_token = await service.login(session, login_user, redis_client)
    response = JSONResponse(content={"message": "Вход успешен"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response


@auth_router.get(
    '/refresh',
    name='refresh',
    summary="Обновляет токены авторизации",
    description=
    """
    Обновляет сессию авторизации
    """,
    status_code=status.HTTP_200_OK,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Успешное обновление токенов'
        ),
        **error_response_docs(
            error=HttpInvalidTokenTypeException
        ),
        **error_response_docs(
            error=HttpTokenIsInvalidException
        )
    }
)
async def refresh(
        request: Request,
        redis_client: RedisDepends(),
        service: Annotated[UserService, Depends(UserService)],
):
    """Обновляет сессию пользователя в системе

    Args:
        request: Запрос
        redis_client: Клиент Redis для хранения сессий
        service: Сервис для работы с пользователями

    Returns:
        RedirectResponse: Возвращает пользователя в путь по параметру

    Raises:
        HTTPException: 401 при ошибках токена
    """
    redirect_url = request.query_params.get("redirect_url", "/")
    try:
        access_token, refresh_token = await service.refresh_token(
            refresh_token=request.cookies.get("refresh_token"),
            redis_client=redis_client
        )
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        return response
    except HTTPException:
        response = RedirectResponse(url=redirect_url)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


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
    await service.logout_user(user, redis_client)
    response = JSONResponse(content={"message": "Вы успешно вышли из системы"})
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return response


auth_templates_routes = APIRouter(
    tags=['templates'],
)

@auth_templates_routes.get(
    path="/login",
    name='login_template',
    summary="Отрисовывает страницу login",
    response_class=HTMLResponse
)
async def login_template(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='auth/login.html'
    )

@auth_templates_routes.get(
    path="/register",
    name='register_template',
    summary="Отрисовывает страницу register",
    response_class=HTMLResponse
)
async def login_template(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='auth/register.html'
    )
