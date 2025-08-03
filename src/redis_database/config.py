from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class RedisConfig(BaseSettings):
    """Класс конфигурации Redis.

    Загружает настройки из .env файла и предоставляет:
    - Параметры подключения к Redis
    - Свойство для формирования URL подключения

    Attributes:
        REDIS_PORT (int): Порт Redis сервера
        REDIS_HOST (str): Хост Redis сервера
        REDIS_PASSWORD (str): Пароль для аутентификации
        REDIS_DB (int): Номер базы данных (по умолчанию 0)
    """
    REDIS_PORT: int
    REDIS_HOST: str
    REDIS_PASSWORD: str
    REDIS_DB: int = 0

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

    @property
    def redis_url(self):
        """Формирует URL для подключения к Redis.

        Формат URL:
        redis://:<password>@<host>:<port>/<db_number>

        Returns:
            str: Полный URL для подключения к Redis
        """
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
