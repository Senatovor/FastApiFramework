from sqladmin import ModelView

from ..auth.models import User


class UserAdmin(ModelView, model=User):
    """View-модель пользователя для SQL админки"""
    column_list = [
        User.id,
        User.username,
        User.email,
        User.is_active,
        User.is_superuser,
        User.is_verified,
    ]
