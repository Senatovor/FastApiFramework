from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse

from ..auth.dependencies import get_current_user
from ..auth.schemes import UserData
from ..config import templates
from ..utils import ok_response_docs

admin_template_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@admin_template_router.get(
    '/sessions_management',
    name='sessions_management',
    summary="Отрисовывает страницу админа сессий",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
    responses={
        **ok_response_docs(
            status_code=status.HTTP_200_OK,
            description='Страница отрисовалась'
        ),
    }
)
async def sessions_management(
        request: Request,
        user: Annotated[UserData, Depends(get_current_user)],
):
    return templates.TemplateResponse(
        request=request,
        name='admin/session_management.html',
        context={
            'user': UserData.model_validate(user),
        }
    )
