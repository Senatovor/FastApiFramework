# Фреймворк для создания веб-приложений в FastAPI

## 📌 Основные возможности

- 🔐 JWT аутентификация (access и refresh токены в cookies)
- 📝 Регистрация пользователей с валидацией данных
- 🔄 Обновление токенов через refresh token
- 🏦 Хранение сессий в Redis
- 🛡️ Middleware для проверки токенов
- 🗃️ CRUD операции для пользователей через SQLAlchemy
- 📊 Логирование всех операций (а также удобная настройка через loguru)
- 🔎 Утилиты для документации API
- 🔄 Асинхронная работа
- 🐳 Docker
- 👀 Пара пробных страниц авторизации

## 🏗️ Структура проекта
```text
src/  
├── auth/  
│   ├── dependencies.py       # Зависимости для аутентификации  
│   ├── exceptions.py         # Кастомные исключения авторизации  
│   ├── handler.py            # Обработчик аутентификации  
│   ├── managers.py           # Менеджер пользователей  
│   ├── middleware.py         # Middleware для проверки токенов  
│   ├── models.py             # Модель пользователя  
│   ├── router.py             # Роутер для эндпоинтов аутентификации  
│   ├── schemes.py            # Pydantic схемы авторизации  
│   ├── config.py             # Конфигурация авторизации  
│   └── services.py           # Сервис для работы с пользователями  
├── database/  
│   ├── manager.py            # Базовый CRUD менеджер  
│   ├── model.py              # Базовая модель SQLAlchemy  
│   ├── config.py             # Конфигурация бд  
│   └── session.py            # Менеджер сессий БД  
├── redis_database/  
│   ├── client.py             # Клиент Redis  
│   └── config.py             # Конфигурация Redis  
├── exceptions.py             # Кастомные общие исключения  
├── log.py                    # Логирование  
├── schemes.py                # Общие Pydantic схемы  
├── main.py                   # Входной файл для запуска  
├── utils.py                  # Общие утилиты (например, помощники для создания документация API)  
└── config.py                 # Основной конфиг  
```
## 🛠️ Технологический стек

- FastAPI - веб-фреймворк
- SQLAlchemy - ORM для работы с базой данных
- asyncpg - асинхронный драйвер PostgreSQL
- Redis - хранилище сессий
- JWT - токены аутентификации
- Pydantic - валидация данных
- Loguru - логирование
- Alembic - миграции базы данных
- Celery - асинхронные задачи (опционально)

## 🚀 Быстрый старт

1. Настройте переменные окружения в .env файле
2. Запустите докер: **docker-compose up -d**


## 🧠 Принципы работы авторизации
1. Регистрация:
   - Пароль хешируется с помощью bcrypt
   - Пользователь сохраняется в базу данных
   - Проверяется уникальность username и email

2. Вход:
   - Проверяются учетные данные
   - Генерируются JWT токены
   - Сессия сохраняется в Redis

3. Проверка токенов:
   - Access token проверяется при каждом запросе (если он не в списке public routes в auth/config)
   - При просрочке access token переправляет на refresh, после чего возвращает обратно
   - Если есть токен, не дает перейти в login и register

4. Выход:
   - Удаляется сессия из Redis
   - Очищаются cookies с токенами

## 💡 Примеры использования
Для просмотра более подробного использования можете использовать этот репозиторий: ВСТАВИТЬ ССЫЛКУ

### Получение текущего пользователя и защита маршрута
```python
from fastapi import APIRouter, Depends
from typing import Annotated

from ..auth.dependencies import get_current_user
from ..auth.schemes import UserData

users_router = APIRouter(
    prefix='/users',
    tags=['users'],
)

@users_router.get(
    '/info',
    name='users-info',
    response_model=UserData,
    summary="Получение текущего юзера",
)
async def user_info(user: Annotated[UserData, Depends(get_current_user)]):
    return user
```
### Зависимости сессий Redis и SQL базы для FastAPI
```python
async def login(
        login_user: LoginUser,
        session: DbSessionDepends(),
        redis_client: RedisDepends(),
        service: Annotated[UserService, Depends(UserService)],
):
```
### Работа CRUD:
```python
from src.database.manager import BaseManager

class UserManager(BaseManager):
    """Менеджер пользователей"""
    model = User


class UserService:

    def __init__(
            self,
            manager: Annotated[UserManager, Depends(UserManager)],
    ) -> None:
        self.manager = manager

    async def login(
            self,
            db_session: AsyncSession,
            login_user: LoginUser,
            redis_client: Redis
    ):
        user = await self.manager.find_one_by(
            db_session,
            UsernameUser(username=login_user.username)  # Pydantic модель
        )
        await redis_client.set(
            f"session:{str(user.id)}",
            str(user.id),
        )
```
Для большего ознакомления можете посмотреть этот [репозиторий моего SQL-фреймворка](https://github.com/Senatovor/BigSQLAss.ync)

### Документирование ответов эндпоинта
```python
@auth_router.post(
    '/register',
    responses={
        **ok_response_docs(
            status_code=status.HTTP_201_CREATED,
            description='Пользователь успешно создан'
        ),
        **error_response_docs(
            error=HttpAlreadyExistException     # ЭТО HTTP ОШИБКА (см. ниже)
        ),
        **error_response_docs(
            error=HttpServerException
        )
    }
)
```


## 📈 Миграции базы данных

Используйте Alembic для управления миграциями:

1. Инициализация:
alembic init migrations
2. Создание миграции:
alembic revision --autogenerate -m "init"
3. Применение миграций:
alembic upgrade head


## 📦 Дополнительные возможности

### Кастомные исключения
Все ошибки аутентификации возвращают стандартизированные ответы:
```python
HttpNotAuthException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Вы не вошли в систему',
    headers={'WWW-Authenticate': 'Bearer'},
)
```
### Логирование
Все операции логируются с помощью Loguru:
```python
logger.info(f"Пользователь {register_user.username} регистрируется...")
```
### Redis сессии
Сессии хранятся в Redis с ключами вида session:{user_id}:
```python
await redis_client.set(f"session:{str(user.id)}", str(user.id))
```

### Возможность редактирования
Вы можете редактировать проект под свой лад! Из простого, если вы хотите отказаться от авторизации, то просто уберите эти две строчки кода в файле main:  
```python
app.add_middleware(TokenValidationMiddleware)
app.include_router(auth_router)
```
Стартовая точка проекта - main, там вы можете посмотреть и редактировать какие модули вам нужны
