from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
from typing import Sequence, TypeVar, Generic
from pydantic import BaseModel
from uuid import UUID
from loguru import logger

from ..database.model import Base

T = TypeVar('T', bound=Base)


class BaseManager(Generic[T]):
    """Базовый сервис для CRUD-операций с SQLAlchemy моделями.

    Реализует стандартные операции создания, чтения, обновления и удаления записей
    для любой модели SQLAlchemy. Работает через асинхронные сессии и поддерживает
    фильтрацию через Pydantic модели.

    Attributes:
        model: Класс SQLAlchemy модели, с которой работает сервис

    Methods:
        add: Создание новой записи
        add_all: Массовое создание записей
        find_by_id: Поиск записи по ID
        find_one_by: Поиск одной записи по фильтрам
        find_all: Поиск всех записей по фильтрам
        update_by_id: Обновление записи по ID
        update_all: Массовое обновление записей
        delete_by_id: Удаление записи по ID
        delete_all: Массовое удаление записей
    """
    model = type[T]

    def __init__(self):
        """Инициализация базового сервиса.

        Raises:
            ValueError: Если модель не указана в дочернем классе
        """
        if not hasattr(self, 'model') or self.model is None:
            raise ValueError("Модель должна быть указана в дочернем классе")

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel) -> model:
        """Создает новую запись в базе данных.

        Args:
            session: Асинхронная сессия SQLAlchemy
            values: Pydantic модель с данными для создания

        Returns:
            T: Созданный экземпляр модели

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Добавление записи {cls.model.__name__} с параметрами: {values_dict}")
        try:
            new_object = cls.model(**values_dict)
            session.add(new_object)
            await session.flush()
            logger.info(f"Запись {cls.model.__name__} успешно добавлена.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении записи: {e}")
            raise e
        return new_object

    @classmethod
    async def add_all(cls, session: AsyncSession, instances: list[BaseModel]) -> Sequence[model]:
        """Массово создает записи в базе данных.

        Args:
            session: Асинхронная сессия SQLAlchemy
            instances: Список Pydantic моделей для создания

        Returns:
            Sequence[T]: Список созданных экземпляров моделей

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        instances_list = [instance.model_dump(exclude_unset=True) for instance in instances]
        logger.info(f"Добавление нескольких записей {cls.model.__name__}. Количество: {len(instances)}")
        try:
            new_objects = [cls.model(**values) for values in instances_list]
            session.add_all(new_objects)
            await session.flush()
            logger.info(f"Записи добавились")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении записей: {e}")
            raise e
        return new_objects

    @classmethod
    async def find_by_id(cls, session: AsyncSession, index: int | UUID) -> model:
        """Находит запись по первичному ключу.

        Args:
            session: Асинхронная сессия SQLAlchemy
            index: ID или UUID записи

        Returns:
            find_object: Найденный экземпляр модели или None

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        try:
            find_object = await session.get(cls.model, index)
            logger.info(f"Запись {cls.model.__name__} с ID {index} найдена")
            return find_object
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи с ID {index}: {e}")
            raise e

    @classmethod
    async def find_one_by(cls, session: AsyncSession, filters: BaseModel | None = None) -> model | None:
        """Находит одну запись по фильтрам.

        Args:
            session: Асинхронная сессия SQLAlchemy
            filters: Pydantic модель для фильтрации (опционально)

        Returns:
            T: Найденный экземпляр модели или None

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        if filters:
            filters_dict = filters.model_dump(exclude_unset=True)
        else:
            filters_dict = {}
        logger.info(f"Поиск одной записи {cls.model.__name__} по фильтрам: {filters_dict}")
        try:
            query = select(cls.model).filter_by(**filters_dict)
            result = await session.execute(query)
            find_object = result.scalar_one_or_none()
            logger.info(f"Запись {'найдена' if find_object else 'не найдена'} по фильтрам: {filters_dict}")
            return find_object
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи по фильтрам {filters_dict}: {e}")
            raise e

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None = None) -> Sequence[model]:
        """Находит все записи по фильтрам.

        Args:
            session: Асинхронная сессия SQLAlchemy
            filters: Pydantic модель для фильтрации (опционально)

        Returns:
            Sequence[T]: Список найденных экземпляров моделей

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        if filters:
            filters_dict = filters.model_dump(exclude_unset=True)
        else:
            filters_dict = {}
        logger.info(f"Поиск записей {cls.model.__name__} по фильтрам: {filters_dict}")
        try:
            query = select(cls.model).filter_by(**filters_dict)
            result = await session.execute(query)
            find_objects = result.scalars().all()
            logger.info(f"Записи {'найдены' if find_objects else 'не найдены'} по фильтрам: {filters_dict}")
            return find_objects
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записей по фильтрам {filters_dict}: {e}")
            raise e

    @classmethod
    async def update_by_id(cls, session: AsyncSession, index: int | UUID, values: BaseModel):
        """Обновляет запись по ID.

        Args:
            session: Асинхронная сессия SQLAlchemy
            index: ID или UUID записи
            values: Pydantic модель с новыми значениями

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Обновление записи {cls.model.__name__} по ID: {index}")
        try:
            find_object = await session.get(cls.model, index)
            for key, value in values_dict.items():
                setattr(find_object, key, value)
            await session.flush()
            logger.info(f"Обновлена запись {cls.model.__name__} по ID: {index}.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении записи: {e}")
            raise e

    @classmethod
    async def update_all(cls, session: AsyncSession, values: BaseModel, filters: BaseModel | None = None):
        """Массово обновляет записи по фильтрам.

        Args:
            session: Асинхронная сессия SQLAlchemy
            values: Pydantic модель с новыми значениями
            filters: Pydantic модель для фильтрации (опционально)

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        values_dict = values.model_dump(exclude_unset=True)
        if filters:
            filters_dict = filters.model_dump(exclude_unset=True)
        else:
            filters_dict = {}
        logger.info(f"Обновление записей {cls.model.__name__} по фильтру: {filters_dict} с параметрами: {values_dict}")
        try:
            query = (
                update(cls.model)
                .where(**filters_dict)
                .values(**values_dict)
            )
            result = await session.execute(query)
            await session.flush()
            logger.info(f"Обновлено {result.rowcount} записей.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении записей: {e}")
            raise e

    @classmethod
    async def delete_by_id(cls, session: AsyncSession, index: int | UUID):
        """Удаляет запись по ID.

        Args:
            session: Асинхронная сессия SQLAlchemy
            index: ID или UUID записи

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        logger.info(f"Удаление записи {cls.model.__name__} по ID: {index}")
        try:
            delete_object = await session.get(cls.model, index)
            await session.delete(delete_object)
            await session.flush()
            logger.info(f"Запись была удалена")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении записи: {e}")
            raise e

    @classmethod
    async def delete_all(cls, session, filters: BaseModel | None = None):
        """Массово удаляет записи по фильтрам.

        Args:
            session: Асинхронная сессия SQLAlchemy
            filters: Pydantic модель для фильтрации (опционально)

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        if filters:
            filters_dict = filters.model_dump(exclude_unset=True)
        else:
            filters_dict = {}
        logger.info(f"Удаление записей {cls.model.__name__} по фильтру: {filters_dict}")
        try:
            query = delete(cls.model).filter_by(**filters_dict)
            result = await session.execute(query)
            await session.flush()
            logger.info(f"Удалено {result.rowcount} записей.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении записей: {e}")
            raise e

    @classmethod
    async def count(cls, session: AsyncSession, filters: BaseModel | None = None):
        """Подсчитывает количество записей модели в базе данных с возможностью фильтрации.

        Args:
            session: Асинхронная сессия SQLAlchemy для работы с БД
            filters: Pydantic модель с параметрами фильтрации (опционально)

        Returns:
            int: Количество найденных записей, удовлетворяющих фильтрам

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных
        """
        filters_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f"Подсчет количества записей {cls.model.__name__} по фильтру: {filters_dict}")
        try:
            query = select(func.count(cls.model.id)).filter_by(**filters_dict)
            result = await session.execute(query)
            count = result.scalar()
            logger.info(f"Найдено {count} записей.")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при подсчете записей: {e}")
            raise
