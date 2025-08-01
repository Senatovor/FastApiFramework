# Фреймворк на FastAPI для быстрого старта

## В комплекте идет:  
1. Готовая OAuth2, JWT, Bearer авторизация  
2. Логирование через loguru  
3. Докер  
4. Модуль для работы с базой данных  

## Алгоритм развертки:
1. Заполнить .env и .env.keycloak файлы
2. ```docker-compose up -d```
3. ```docker-compose exec app bash```
4. ```alembic revision --autogenerate -m "create  user"```
5. ```alembic upgrade head```
6. ```exit```