"""
Management command для создания тестовых пользователей.

Использование:
    python manage.py create_test_users
"""

from django.core.management.base import BaseCommand

from shift_report.models import (Employee, EmployeeRole, Sector, Workplace,
                                 Workshop)


class Command(BaseCommand):
    help = 'Создание тестовых пользователей для разработки'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых пользователей...')

        # Создаём структуру подразделений если её нет
        workshop, _ = Workshop.objects.get_or_create(
            number=1,
            defaults={'name': 'Механический цех'}
        )

        sector, _ = Sector.objects.get_or_create(
            workshop=workshop,
            number=1,
            defaults={'name': 'Участок сборки'}
        )

        workplace, _ = Workplace.objects.get_or_create(
            sector=sector,
            number=1,
            defaults={
                'name': 'Сборочный стенд №1',
                'passport_capacity': 10
            }
        )

        # Создаём пользователей
        users_data = [
            {
                'personnel_number': '100001',
                'pin': '1234',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'middle_name': 'Сергеевич',
                'role': EmployeeRole.OPERATOR,
                'workplace': workplace,
            },
            {
                'personnel_number': '100002',
                'pin': '1234',
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'middle_name': 'Александровна',
                'role': EmployeeRole.MASTER,
                'sector': sector,
            },
            {
                'personnel_number': '100003',
                'pin': '1234',
                'first_name': 'Алексей',
                'last_name': 'Козлов',
                'middle_name': 'Владимирович',
                'role': EmployeeRole.CHIEF,
                'workshop': workshop,
            },
            {
                'personnel_number': '100000',
                'pin': '0000',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'middle_name': '',
                'role': EmployeeRole.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
        ]

        for user_data in users_data:
            pin = user_data.pop('pin')
            personnel_number = user_data['personnel_number']

            user, created = Employee.objects.get_or_create(
                personnel_number=personnel_number,
                defaults=user_data
            )

            if created:
                user.set_pin(pin)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Создан: {user.get_full_name()} '
                        f'({personnel_number}) - {user.get_role_display()}'
                    )
                )
            else:
                self.stdout.write(
                    f'  Уже существует: {user.get_full_name()} ({personnel_number})'
                )

        self.stdout.write(self.style.SUCCESS('\nТестовые пользователи:'))
        self.stdout.write('  Оператор:      100001 / PIN: 1234')
        self.stdout.write('  Мастер:        100002 / PIN: 1234')
        self.stdout.write('  Начальник:     100003 / PIN: 1234')
        self.stdout.write('  Администратор: 100000 / PIN: 0000')
