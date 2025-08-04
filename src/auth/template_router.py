from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from src.auth.dependencies import have_tokens_in_cookies
from src.config import config, templates

auth_templates_routes = APIRouter(
    tags=['templates'],
)


@auth_templates_routes.get(
    path="/login",
    name='login_template',
    summary="Отрисовывает страницу login",
    response_class=HTMLResponse
)
async def login_template(
        request: Request,
        flag: Annotated[bool, Depends(have_tokens_in_cookies)]
):
    if flag:
        return RedirectResponse(url=config.auth_config.HOME_ROUTE)
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
async def register_template(
        request: Request,
        flag: Annotated[bool, Depends(have_tokens_in_cookies)]
):
    if flag:
        return RedirectResponse(url=config.auth_config.HOME_ROUTE)
    return templates.TemplateResponse(
        request=request,
        name='auth/register.html'
    )
