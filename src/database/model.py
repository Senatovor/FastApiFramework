from sqlalchemy import func, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, class_mapper
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime
import uuid


class Base(AsyncAttrs, DeclarativeBase):
    """Абстрактный базовый класс для всех моделей SQLAlchemy

    Attributes:
        id: ID таблицы
        created_at: Время создания
        updated_at: Время обновления
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Перевод названия класса в название таблицы"""
        return cls.__name__.lower() + 's'

    def to_dict(self) -> dict:
        """Универсальный метод для конвертации объекта SQLAlchemy в словарь"""
        columns = class_mapper(self.__class__).columns
        return {column.key: getattr(self, column.key) for column in columns}

    def __repr__(self) -> str:
        """Строковое представление объекта"""
        return f"<{self.__class__.__name__}(id={self.id})>"
