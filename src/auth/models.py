from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text, Boolean, String

from ..database.model import Base


class User(Base):
    """ORM-модель пользователя системы.

    Attributes:
        username (str): Логин пользователя. Обязательное поле.
        email (str): Электронная почта пользователя. Должна быть уникальной.
        password (str): Хэшированный пароль пользователя. Хранится в зашифрованном виде.
        is_active (bool): Флаг активности пользователя. По умолчанию False.
        is_superuser (bool): Флаг суперпользователя. По умолчанию False.
        is_verified (bool): Флаг подтверждения пользователя. По умолчанию False.
        # role (str): Роль пользователя в системе. По умолчанию 'user'.
    """
    username: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment='Логин пользователя'
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Электронная почта пользователя"
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='Хэшированный пароль пользователя'
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
        comment="Флаг активности пользователя"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
        comment="Флаг суперпользователя (полный доступ)"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
        comment="Флаг подтверждения email пользователя"
    )

    # role: Mapped[str] = mapped_column(
    #     default='user',
    #     server_default=text('user'),
    #     nullable=False,
    # )
