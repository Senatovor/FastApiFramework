from fastapi import status

from ..exceptions import BaseAppException


class NotAuthException(BaseAppException):
    """Исключение для ошибок авторизации"""
    status_code = status.HTTP_401_UNAUTHORIZED
    details = 'Вы не вошли в систему'
    headers = {'WWW-Authenticate': 'Bearer'}


class AlreadyExistException(BaseAppException):
    """Исключение для ошибки создания уже существующего юзера"""
    status_code = status.HTTP_409_CONFLICT
    details = "Такой пользователь уже есть"
