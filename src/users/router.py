from fastapi import APIRouter, Depends
from typing import Annotated

from ..auth.dependencies import get_current_user
from ..auth.schemes import UserData

users_router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@users_router.get(
    '/info',
    name='users-info',
    response_model=UserData,
    summary="Получение текущего юзера",
)
async def user_info(user: Annotated[UserData, Depends(get_current_user)]):
    return user