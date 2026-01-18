"""
Management command для создания тестовых данных.

Использование:
    python manage.py create_test_data
"""

from datetime import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from shift_report.models import (DeviationGroup, DeviationReason, Employee,
                                 EmployeeRole, Product, Sector, Shift,
                                 Workplace, Workshop)
from shift_report.services import BlankGeneratorService


class Command(BaseCommand):
    help = 'Создание тестовых данных для разработки'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...\n')

        # 1. Создаём структуру подразделений
        self.stdout.write('1. Создание подразделений...')

        workshop, _ = Workshop.objects.get_or_create(
            number=1,
            defaults={'name': 'Механический цех'}
        )

        sector, _ = Sector.objects.get_or_create(
            workshop=workshop,
            number=1,
            defaults={'name': 'Участок сборки'}
        )

        workplace1, _ = Workplace.objects.get_or_create(
            sector=sector,
            number=1,
            defaults={
                'name': 'Сборочный стенд №1',
                'equipment_type': 'Сборочный стенд',
                'passport_capacity': 12,
                'achieved_capacity': 10,
            }
        )

        workplace2, _ = Workplace.objects.get_or_create(
            sector=sector,
            number=2,
            defaults={
                'name': 'Сборочный стенд №2',
                'equipment_type': 'Сборочный стенд',
                'passport_capacity': 15,
                'achieved_capacity': 12,
            }
        )

        self.stdout.write(self.style.SUCCESS('   ✓ Подразделения созданы'))

        # 2. Создаём смены
        self.stdout.write('2. Создание смен...')

        shift1, _ = Shift.objects.get_or_create(
            number=1,
            defaults={
                'name': 'Первая смена',
                'start_time': time(8, 0),
                'end_time': time(20, 0),
                'lunch_break': 30,
                'personal_break': 10,
                'handover_break': 10,
            }
        )

        shift2, _ = Shift.objects.get_or_create(
            number=2,
            defaults={
                'name': 'Вторая смена',
                'start_time': time(20, 0),
                'end_time': time(8, 0),
                'lunch_break': 30,
                'personal_break': 10,
                'handover_break': 10,
            }
        )

        self.stdout.write(self.style.SUCCESS('   ✓ Смены созданы'))

        # 3. Создаём продукцию
        self.stdout.write('3. Создание продукции...')

        product1, _ = Product.objects.get_or_create(
            article='КП-001',
            defaults={
                'name': 'Корпус прибора',
                'unit': 'шт.',
                'takt_time': 360,  # 6 минут = 10 шт/час
                'cycle_time': 340,
            }
        )

        product2, _ = Product.objects.get_or_create(
            article='БП-002',
            defaults={
                'name': 'Блок питания',
                'unit': 'шт.',
                'takt_time': 300,  # 5 минут = 12 шт/час
                'cycle_time': 280,
            }
        )

        self.stdout.write(self.style.SUCCESS('   ✓ Продукция создана'))

        # 4. Создаём группы причин и причины
        self.stdout.write('4. Создание причин отклонений...')

        # Группа: Организационные
        org_group, _ = DeviationGroup.objects.get_or_create(
            code='ORG',
            defaults={
                'name': 'Организационные',
                'color': '#17a2b8',
                'order': 1,
            }
        )

        org_reasons = [
            ('ORG-01', 'Отсутствие оператора'),
            ('ORG-02', 'Отсутствие задания'),
            ('ORG-03', 'Совещание/обучение'),
            ('ORG-04', 'Уборка рабочего места'),
        ]

        for code, name in org_reasons:
            DeviationReason.objects.get_or_create(
                code=code,
                defaults={
                    'group': org_group,
                    'name': name,
                }
            )

        # Группа: Технические
        tech_group, _ = DeviationGroup.objects.get_or_create(
            code='TECH',
            defaults={
                'name': 'Технические',
                'color': '#dc3545',
                'order': 2,
            }
        )

        tech_reasons = [
            ('TECH-01', 'Поломка оборудования'),
            ('TECH-02', 'Настройка оборудования'),
            ('TECH-03', 'Замена инструмента'),
            ('TECH-04', 'Плановое ТО'),
        ]

        for code, name in tech_reasons:
            DeviationReason.objects.get_or_create(
                code=code,
                defaults={
                    'group': tech_group,
                    'name': name,
                }
            )

        # Группа: Нет поставок
        supply_group, _ = DeviationGroup.objects.get_or_create(
            code='SUPPLY',
            defaults={
                'name': 'Нет поставок',
                'color': '#ffc107',
                'order': 3,
            }
        )

        supply_reasons = [
            ('SUP-01', 'Нет комплектующих'),
            ('SUP-02', 'Нет материалов'),
            ('SUP-03', 'Нет тары/упаковки'),
        ]

        for code, name in supply_reasons:
            DeviationReason.objects.get_or_create(
                code=code,
                defaults={
                    'group': supply_group,
                    'name': name,
                }
            )

        # Группа: Качество
        quality_group, _ = DeviationGroup.objects.get_or_create(
            code='QUALITY',
            defaults={
                'name': 'Качество',
                'color': '#6f42c1',
                'order': 4,
            }
        )

        quality_reasons = [
            ('QA-01', 'Брак комплектующих'),
            ('QA-02', 'Доработка изделий'),
            ('QA-03', 'Контроль качества'),
        ]

        for code, name in quality_reasons:
            DeviationReason.objects.get_or_create(
                code=code,
                defaults={
                    'group': quality_group,
                    'name': name,
                }
            )

        self.stdout.write(self.style.SUCCESS('   ✓ Причины отклонений созданы'))

        # 5. Создаём пользователей
        self.stdout.write('5. Создание пользователей...')

        users_data = [
            {
                'personnel_number': '100001',
                'pin': '1234',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'middle_name': 'Сергеевич',
                'role': EmployeeRole.OPERATOR,
                'workplace': workplace1,
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

        admin_user = None
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

            if user.role == EmployeeRole.ADMIN:
                admin_user = user

        self.stdout.write(self.style.SUCCESS('   ✓ Пользователи созданы'))

        # 6. Создаём бланки на сегодня
        self.stdout.write('6. Создание бланков ПА...')

        today = timezone.localdate()
        service = BlankGeneratorService()

        # Бланк для РМ1
        try:
            blank1 = service.create_blank(
                workplace=workplace1,
                date=today,
                shift=shift1,
                product=product1,
                planned_quantity=100,
                created_by=admin_user,
            )
            self.stdout.write(f'   Создан бланк: {blank1}')
        except ValueError as e:
            self.stdout.write(f'   Бланк для РМ1 уже существует: {e}')

        # Бланк для РМ2
        try:
            blank2 = service.create_blank(
                workplace=workplace2,
                date=today,
                shift=shift1,
                product=product2,
                planned_quantity=120,
                created_by=admin_user,
            )
            self.stdout.write(f'   Создан бланк: {blank2}')
        except ValueError as e:
            self.stdout.write(f'   Бланк для РМ2 уже существует: {e}')

        self.stdout.write(self.style.SUCCESS('   ✓ Бланки созданы'))

        # Итоги
        self.stdout.write('\n' + self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

        self.stdout.write('\nТестовые пользователи:')
        self.stdout.write('  Оператор:      100001 / PIN: 1234')
        self.stdout.write('  Мастер:        100002 / PIN: 1234')
        self.stdout.write('  Начальник:     100003 / PIN: 1234')
        self.stdout.write('  Администратор: 100000 / PIN: 0000')

        self.stdout.write('\nДля входа перейдите на http://localhost:8000/login/')
