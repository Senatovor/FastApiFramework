from pydantic import BaseModel, EmailStr, Field, SecretStr, ConfigDict
import datetime
import uuid


class UsernameUser(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=8,
        description='Имя пользователя'
    )


class EmailUser(BaseModel):
    email: EmailStr = Field(description='Почта пользователя')


class PasswordUser(BaseModel):
    password: SecretStr = Field(description='Введенный пароль')


class LoginUser(PasswordUser, UsernameUser):
    pass


class RegistrateUser(LoginUser, EmailUser):
    pass


class UserData(EmailUser, UsernameUser):
    id: uuid.UUID | str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
