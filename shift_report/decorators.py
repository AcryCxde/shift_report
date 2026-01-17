"""
Декораторы для проверки прав доступа.

FR-039: Ролевая модель доступа
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    """
    Декоратор для проверки роли пользователя.

    Использование:
        @role_required('operator', 'master')
        def my_view(request):
            ...

    Args:
        *roles: Разрешённые роли ('operator', 'master', 'chief', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Админы имеют доступ ко всему
            if request.user.is_admin or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Проверяем роль
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, 'У вас нет доступа к этой странице')
            return redirect('home')

        return wrapper
    return decorator


def operator_required(view_func):
    """Декоратор для операторов и выше"""
    return role_required('operator', 'master', 'chief', 'admin')(view_func)


def master_required(view_func):
    """Декоратор для мастеров и выше"""
    return role_required('master', 'chief', 'admin')(view_func)


def chief_required(view_func):
    """Декоратор для начальников и выше"""
    return role_required('chief', 'admin')(view_func)


def admin_required(view_func):
    """Декоратор только для администраторов"""
    return role_required('admin')(view_func)


class RoleRequiredMixin:
    """
    Миксин для class-based views для проверки ролей.

    Использование:
        class MyView(RoleRequiredMixin, View):
            allowed_roles = ['operator', 'master']
    """

    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Админы имеют доступ ко всему
        if request.user.is_admin or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Проверяем роль
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            messages.error(request, 'У вас нет доступа к этой странице')
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


class OperatorRequiredMixin(RoleRequiredMixin):
    """Миксин для операторов и выше"""
    allowed_roles = ['operator', 'master', 'chief', 'admin']


class MasterRequiredMixin(RoleRequiredMixin):
    """Миксин для мастеров и выше"""
    allowed_roles = ['master', 'chief', 'admin']


class ChiefRequiredMixin(RoleRequiredMixin):
    """Миксин для начальников и выше"""
    allowed_roles = ['chief', 'admin']


class AdminRequiredMixin(RoleRequiredMixin):
    """Миксин только для администраторов"""
    allowed_roles = ['admin']
