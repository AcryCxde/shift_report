from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db.models import (SET_NULL, BooleanField, CharField, DateTimeField,
                              ForeignKey, TextChoices)


class EmployeeRole(TextChoices):
    """Роли пользователей в системе"""
    OPERATOR = 'operator', 'Оператор'
    MASTER = 'master', 'Мастер'
    CHIEF = 'chief', 'Начальник'
    ADMIN = 'admin', 'Администратор'


class EmployeeManager(BaseUserManager):
    """Менеджер для создания пользователей"""

    def create_user(self, personnel_number, pin, **extra_fields):
        if not personnel_number:
            raise ValueError('Табельный номер обязателен')
        user = self.model(personnel_number=personnel_number, **extra_fields)
        user.set_pin(pin)
        user.save(using=self._db)
        return user

    def create_superuser(self, personnel_number, pin, **extra_fields):
        extra_fields.setdefault('role', EmployeeRole.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(personnel_number, pin, **extra_fields)


class Employee(AbstractBaseUser):
    """
    Сотрудник (пользователь системы)

    Расширенная модель пользователя с:
    - Табельным номером вместо username
    - PIN-кодом вместо пароля
    - Ролями и привязкой к подразделениям
    """

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name']

    # Идентификация
    personnel_number = CharField(
        'Табельный номер',
        max_length=20,
        unique=True,
        help_text='Уникальный табельный номер (6-8 цифр)',
    )

    pin_hash = CharField(
        'PIN-код (хеш)',
        max_length=128,
        help_text='Хранится в зашифрованном виде',
    )

    # ФИО
    last_name = CharField(
        'Фамилия',
        max_length=150,
    )

    first_name = CharField(
        'Имя',
        max_length=150,
    )

    middle_name = CharField(
        'Отчество',
        max_length=150,
        blank=True,
        default='',
    )

    # Роль и доступ
    role = CharField(
        'Роль',
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.OPERATOR,
    )

    # Привязка к подразделениям
    workshop = ForeignKey(
        'shift_report.Workshop',
        verbose_name='Цех',
        related_name='employees',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        help_text='Для начальников цехов и администраторов',
    )

    sector = ForeignKey(
        'shift_report.Sector',
        verbose_name='Участок',
        related_name='employees',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        help_text='Для мастеров',
    )

    workplace = ForeignKey(
        'shift_report.Workplace',
        verbose_name='Рабочее место',
        related_name='employees',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        help_text='Для операторов',
    )

    # Статус
    is_active = BooleanField(
        'Активен',
        default=True,
        help_text='Неактивные сотрудники не могут войти в систему',
    )

    is_staff = BooleanField(
        'Доступ к админке',
        default=False,
    )

    is_superuser = BooleanField(
        'Суперпользователь',
        default=False,
    )

    # Даты
    date_joined = DateTimeField(
        'Дата создания',
        auto_now_add=True,
    )

    last_login = DateTimeField(
        'Последний вход',
        null=True,
        blank=True,
    )

    objects = EmployeeManager()

    USERNAME_FIELD = 'personnel_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'{self.get_full_name()} ({self.personnel_number})'

    def get_full_name(self):
        """Полное ФИО"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    def get_short_name(self):
        """Фамилия И.О."""
        result = self.last_name
        if self.first_name:
            result += f' {self.first_name[0]}.'
        if self.middle_name:
            result += f'{self.middle_name[0]}.'
        return result

    def set_pin(self, raw_pin):
        """Установить PIN-код (хешируется)"""
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        """Проверить PIN-код"""
        return check_password(raw_pin, self.pin_hash)

    def has_perm(self, perm, obj=None):
        """Проверка прав (для совместимости с Django Admin)"""
        return self.is_superuser

    def has_module_perms(self, app_label):
        """Проверка прав на модуль (для совместимости с Django Admin)"""
        return self.is_superuser

    @property
    def is_operator(self):
        return self.role == EmployeeRole.OPERATOR

    @property
    def is_master(self):
        return self.role == EmployeeRole.MASTER

    @property
    def is_chief(self):
        return self.role == EmployeeRole.CHIEF

    @property
    def is_admin(self):
        return self.role == EmployeeRole.ADMIN
