from fastapi import status
from fastapi.exceptions import HTTPException

HttpServerException = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail='Ошибка сервера'
)
