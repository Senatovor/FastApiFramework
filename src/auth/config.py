from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class AuthConfig(BaseSettings):
    """Класс конфигурации авторизации.

    Загружает настройки из .env файла или переменных окружения.

    Attributes:
        SECRET_KEY: Секретный ключ для JWT
        ALGORITHM: Алгоритм шифрования JWT
        ACCESS_TOKEN_EXPIRE: Время жизни access токена (в минутах)
        PUBLIC_ROUTES: Роуты по которым не проверяется авторизация
        LOGIN_ROUTE: Путь входа
        REFRESH_ROUTE: Путь обновления токена
    """
    # Настройки аутентификации
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE: int
    REFRESH_TOKEN_EXPIRE: int

    PUBLIC_ROUTES: list = [
        "/login",
        "/auth/login",
        "/register",
        "/auth/register",
        "/auth/refresh",
        '/openapi.json',
    ]
    LOGIN_ROUTE: str = "/login"
    REFRESH_ROUTE: str = "/auth/refresh"
    HOME_ROUTE: str = "/"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )
