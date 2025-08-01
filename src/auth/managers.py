from ..database.manager import BaseManager
from .models import User


class UserManager(BaseManager):
    """Менеджер пользователей"""
    model = User
