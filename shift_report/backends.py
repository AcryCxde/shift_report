"""
Бэкенд аутентификации для сотрудников.

FR-014: Авторизация оператора (упрощённая)
- Вход по табельному номеру + PIN (4-6 цифр)
- Запоминание устройства (сессия не сбрасывается)
"""

from django.contrib.auth.backends import BaseBackend
from django.utils import timezone

from shift_report.models import Employee


class PINAuthenticationBackend(BaseBackend):
    """
    Бэкенд аутентификации по табельному номеру и PIN-коду.

    Используется вместо стандартного username/password.
    """

    def authenticate(self, request, personnel_number=None, pin=None, **kwargs):
        """
        Аутентификация сотрудника.

        Args:
            request: HTTP запрос
            personnel_number: Табельный номер
            pin: PIN-код (4-6 цифр)

        Returns:
            Employee или None
        """
        if personnel_number is None or pin is None:
            return None

        try:
            employee = Employee.objects.get(
                personnel_number=personnel_number,
                is_active=True
            )
        except Employee.DoesNotExist:
            return None

        if employee.check_pin(pin):
            # Обновляем время последнего входа
            employee.last_login = timezone.now()
            employee.save(update_fields=['last_login'])
            return employee

        return None

    def get_user(self, user_id):
        """
        Получение пользователя по ID.

        Args:
            user_id: ID сотрудника

        Returns:
            Employee или None
        """
        try:
            return Employee.objects.get(pk=user_id, is_active=True)
        except Employee.DoesNotExist:
            return None
