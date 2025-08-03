from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """Класс конфигурации базы данных.

    Загружает настройки из .env файла или переменных окружения.

    Attributes:
        DB_HOST: Хост базы данных
        DB_PORT: Порт базы данных
        POSTGRES_DB: Имя базы данных
        POSTGRES_USER: Пользователь БД
        POSTGRES_PASSWORD: Пароль пользователя БД
    """
    # Настройки базы данных
    DB_HOST: str
    DB_PORT: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Генерирует URL для подключения к PostgreSQL с использованием asyncpg."""
        return (f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@'
                f'{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}')