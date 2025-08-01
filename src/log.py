import logging
from loguru import logger
from pathlib import Path

from .config import config


class InterceptHandler(logging.Handler):
    """Обработчик для перехвата стандартных логов Python и перенаправления их в Loguru.

    Methods:
        emit: Перехватывает и обрабатывает каждое лог-сообщение.
    """
    def emit(self, record):
        """Перехватывает лог-запись и перенаправляет ее в Loguru.

        Args:
            record (logging.LogRecord): Запись лога из стандартной библиотеки logging
        """
        # Получаем соответствующий уровень логирования Loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Ищем место вызова для правильной глубины стека
        frame, depth = logging.currentframe(), 2
        while frame.f_back and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger():
    """Настраивает систему логирования приложения."""

    # Удаляем существующие обработчики логов
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Перехватываем стандартное логирование
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)


    # Настраиваем логирование для внешних библиотек
    loggers = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "asyncio",
        "starlette",
    )

    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = []
        logging_logger.propagate = True

    logger.add(
        Path(__file__).parent.parent / "app.log",
        rotation=config.logger_config.ROTATION,
        level=config.logger_config.LEVEL,
        backtrace=config.logger_config.BACKTRACE,
        diagnose=config.logger_config.DIAGNOSE,
        enqueue=config.logger_config.ENQUEUE,
        catch=config.logger_config.CATCH,
        compression=config.logger_config.COMPRESSION,
    )
