from fastapi import status, HTTPException

HttpNotAuthException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Вы не вошли в систему',
    headers={'WWW-Authenticate': 'Bearer'},
)

HttpAlreadyExistException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail=f'Такой пользователь уже есть'
)

HttpInvalidTokenTypeException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Неверный тип токена"
)

HttpTokenIsInvalidException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Токен недействителен"
)

HttpUserNotFoundException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Пользователь не найден"
)

HttpExpiredSignatureException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Срок действия токена истек"
)

HttpTokenMissingException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Токен отсутствует"
)
