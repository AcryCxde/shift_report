"""
Команда для создания полного набора демо-данных.

Использование:
    python manage.py setup_demo_data

Создаёт:
- Структуру предприятия (цеха, участки, рабочие места)
- Справочники (смены, продукция, причины отклонений)
- Пользователей всех ролей
- Бланки ПА на текущую дату с заполненными данными
- Отклонения и принятые меры
"""

import random
from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from shift_report.models import (DeviationEntry, DeviationGroup,
                                 DeviationReason, Employee, PABlank, PARecord,
                                 Product, Sector, Shift, TakenMeasure,
                                 Workplace, Workshop)
from shift_report.services import BlankGeneratorService


class Command(BaseCommand):
    help = 'Создаёт полный набор демо-данных для тестирования всех функций системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очистка существующих данных...')
            self._clear_data()

        self.stdout.write('Создание демо-данных...')

        # 1. Создаём структуру предприятия
        self.stdout.write('  1. Структура предприятия...')
        workshops = self._create_workshops()
        sectors = self._create_sectors(workshops)
        workplaces = self._create_workplaces(sectors)

        # 2. Создаём справочники
        self.stdout.write('  2. Справочники...')
        shifts = self._create_shifts()
        products = self._create_products()
        groups, reasons = self._create_deviation_reasons()

        # 3. Создаём пользователей
        self.stdout.write('  3. Пользователи...')
        users = self._create_users(workshops, sectors, workplaces)

        # 4. Создаём бланки
        self.stdout.write('  4. Бланки ПА...')
        blanks = self._create_blanks(workplaces, shifts, products, users)

        # 5. Заполняем данные
        self.stdout.write('  5. Заполнение данных и отклонений...')
        self._fill_records(blanks, reasons, users)

        self.stdout.write(self.style.SUCCESS('\n✓ Демо-данные успешно созданы!'))
        self._print_summary(workshops, sectors, workplaces, users, blanks)

    def _clear_data(self):
        """Очистка всех данных."""
        TakenMeasure.objects.all().delete()
        DeviationEntry.objects.all().delete()
        PARecord.objects.all().delete()
        PABlank.objects.all().delete()
        DeviationReason.objects.all().delete()
        DeviationGroup.objects.all().delete()
        Product.objects.all().delete()
        Shift.objects.all().delete()
        Employee.objects.all().delete()
        Workplace.objects.all().delete()
        Sector.objects.all().delete()
        Workshop.objects.all().delete()

    def _create_workshops(self):
        """Создание цехов."""
        workshops = []
        data = [
            (1, 'Сборочный цех', 'Основное сборочное производство'),
            (2, 'Механический цех', 'Механообработка деталей'),
            (3, 'Упаковочный цех', 'Упаковка готовой продукции'),
        ]
        for number, name, desc in data:
            ws, _ = Workshop.objects.get_or_create(
                number=number,
                defaults={'name': name, 'description': desc}
            )
            workshops.append(ws)
        return workshops

    def _create_sectors(self, workshops):
        """Создание участков."""
        sectors = []
        data = [
            # Сборочный цех
            (workshops[0], 1, 'Участок сборки №1', 'Сборка основных узлов'),
            (workshops[0], 2, 'Участок сборки №2', 'Сборка вспомогательных узлов'),
            (workshops[0], 3, 'Участок тестирования', 'Контроль качества сборки'),
            # Механический цех
            (workshops[1], 1, 'Токарный участок', 'Токарная обработка'),
            (workshops[1], 2, 'Фрезерный участок', 'Фрезерная обработка'),
            # Упаковочный цех
            (workshops[2], 1, 'Линия упаковки', 'Упаковка готовой продукции'),
        ]
        for ws, number, name, desc in data:
            sec, _ = Sector.objects.get_or_create(
                workshop=ws,
                number=number,
                defaults={'name': name, 'description': desc}
            )
            sectors.append(sec)
        return sectors

    def _create_workplaces(self, sectors):
        """Создание рабочих мест."""
        workplaces = []
        data = [
            # Участок сборки №1
            (sectors[0], 1, 'Сборочный стенд №1', 'Стенд сборки', 12.0, 11.5),
            (sectors[0], 2, 'Сборочный стенд №2', 'Стенд сборки', 15.0, 14.0),
            (sectors[0], 3, 'Сборочный стенд №3', 'Стенд сборки', 10.0, 9.5),
            # Участок сборки №2
            (sectors[1], 1, 'Стенд вспом. сборки №1', 'Стенд сборки', 20.0, 18.0),
            (sectors[1], 2, 'Стенд вспом. сборки №2', 'Стенд сборки', 20.0, 19.0),
            # Участок тестирования
            (sectors[2], 1, 'Тестовый стенд №1', 'Тестовое оборудование', 8.0, 7.5),
            (sectors[2], 2, 'Тестовый стенд №2', 'Тестовое оборудование', 8.0, 8.0),
            # Токарный участок
            (sectors[3], 1, 'Токарный станок №1', 'Токарный станок ЧПУ', 25.0, 24.0),
            (sectors[3], 2, 'Токарный станок №2', 'Токарный станок ЧПУ', 25.0, 23.0),
            # Фрезерный участок
            (sectors[4], 1, 'Фрезерный станок №1', 'Фрезерный станок ЧПУ', 18.0, 17.0),
            # Линия упаковки
            (sectors[5], 1, 'Упаковочная линия №1', 'Автоматическая линия', 50.0, 48.0),
            (sectors[5], 2, 'Упаковочная линия №2', 'Полуавтоматическая линия', 30.0, 28.0),
        ]
        for sec, number, name, eq_type, passport, achieved in data:
            wp, _ = Workplace.objects.get_or_create(
                sector=sec,
                number=number,
                defaults={
                    'name': name,
                    'equipment_type': eq_type,
                    'passport_capacity': passport,
                    'achieved_capacity': achieved,
                }
            )
            workplaces.append(wp)
        return workplaces

    def _create_shifts(self):
        """Создание смен."""
        shifts = []
        data = [
            (1, 'Первая смена', time(8, 0), time(20, 0), 60),
            (2, 'Вторая смена', time(20, 0), time(8, 0), 60),
            (3, 'Дневная смена', time(9, 0), time(18, 0), 60),
        ]
        for number, name, start, end, break_min in data:
            shift, _ = Shift.objects.get_or_create(
                number=number,
                defaults={
                    'name': name,
                    'start_time': start,
                    'end_time': end,
                    'lunch_break': break_min,
                }
            )
            shifts.append(shift)
        return shifts

    def _create_products(self):
        """Создание продукции."""
        products = []
        data = [
            ('PROD-001', 'Узел сборочный А', 300),
            ('PROD-002', 'Узел сборочный Б', 240),
            ('PROD-003', 'Деталь токарная', 120),
            ('PROD-004', 'Деталь фрезерная', 180),
            ('PROD-005', 'Комплект упакованный', 60),
        ]
        for article, name, takt in data:
            prod, _ = Product.objects.get_or_create(
                article=article,
                defaults={'name': name, 'takt_time': takt}
            )
            products.append(prod)
        return products

    def _create_deviation_reasons(self):
        """Создание групп и причин отклонений."""
        groups = []
        reasons = []

        groups_data = [
            ('ORG', 'Организационные', '#ffc107', 1),
            ('TECH', 'Технические', '#dc3545', 2),
            ('SUPPLY', 'Снабжение', '#17a2b8', 3),
            ('QUALITY', 'Качество', '#6f42c1', 4),
        ]

        for code, name, color, order in groups_data:
            grp, _ = DeviationGroup.objects.get_or_create(
                code=code,
                defaults={'name': name, 'color': color, 'order': order}
            )
            groups.append(grp)

        reasons_data = [
            # Организационные
            ('ORG-01', 'Отсутствие оператора', groups[0]),
            ('ORG-02', 'Обучение персонала', groups[0]),
            ('ORG-03', 'Совещание', groups[0]),
            ('ORG-04', 'Перерыв', groups[0]),
            # Технические
            ('TECH-01', 'Поломка оборудования', groups[1]),
            ('TECH-02', 'Плановое ТО', groups[1]),
            ('TECH-03', 'Переналадка', groups[1]),
            ('TECH-04', 'Отсутствие электроэнергии', groups[1]),
            ('TECH-05', 'Износ инструмента', groups[1]),
            # Снабжение
            ('SUP-01', 'Отсутствие материалов', groups[2]),
            ('SUP-02', 'Ожидание комплектующих', groups[2]),
            ('SUP-03', 'Отсутствие тары', groups[2]),
            # Качество
            ('QUA-01', 'Брак материала', groups[3]),
            ('QUA-02', 'Доработка изделия', groups[3]),
            ('QUA-03', 'Контрольная проверка', groups[3]),
        ]

        for code, name, group in reasons_data:
            reason, _ = DeviationReason.objects.get_or_create(
                code=code,
                defaults={'name': name, 'group': group}
            )
            reasons.append(reason)

        return groups, reasons

    def _create_users(self, workshops, sectors, workplaces):
        """Создание пользователей."""
        users = {}

        # Администратор
        admin, created = Employee.objects.get_or_create(
            personnel_number='100000',
            defaults={
                'first_name': 'Админ',
                'last_name': 'Системы',
                'role': 'admin',
            },
            is_staff=True,
        )
        if created:
            admin.set_pin('0000')
            admin.save()
        users['admin'] = admin

        # Начальники цехов
        chiefs = []
        for i, ws in enumerate(workshops):
            chief, created = Employee.objects.get_or_create(
                personnel_number=f'20000{i + 1}',
                defaults={
                    'first_name': ['Сергей', 'Андрей', 'Дмитрий'][i],
                    'last_name': ['Сидоров', 'Козлов', 'Морозов'][i],
                    'middle_name': 'Владимирович',
                    'role': 'chief',
                    'workshop': ws,
                }
            )
            if created:
                chief.set_pin('1234')
                chief.save()
            chiefs.append(chief)
        users['chiefs'] = chiefs

        # Мастера
        masters = []
        for i, sec in enumerate(sectors):
            master, created = Employee.objects.get_or_create(
                personnel_number=f'30000{i + 1}',
                defaults={
                    'first_name': ['Пётр', 'Николай', 'Алексей', 'Виктор', 'Михаил', 'Евгений'][i],
                    'last_name': ['Петров', 'Николаев', 'Алексеев', 'Викторов', 'Михайлов', 'Евгеньев'][i],
                    'role': 'master',
                    'workshop': sec.workshop,
                    'sector': sec,
                }
            )
            if created:
                master.set_pin('1234')
                master.save()
            masters.append(master)
        users['masters'] = masters

        # Операторы
        operators = []
        for i, wp in enumerate(workplaces):
            op, created = Employee.objects.get_or_create(
                personnel_number=f'10000{i + 1}',
                defaults={
                    'first_name': ['Иван', 'Василий', 'Григорий', 'Олег', 'Павел',
                                   'Роман', 'Степан', 'Тимур', 'Фёдор', 'Юрий', 'Артём', 'Борис'][i],
                    'last_name': ['Иванов', 'Васильев', 'Григорьев', 'Олегов', 'Павлов',
                                  'Романов', 'Степанов', 'Тимуров', 'Фёдоров', 'Юрьев', 'Артёмов', 'Борисов'][i],
                    'role': 'operator',
                    'workshop': wp.sector.workshop,
                    'sector': wp.sector,
                    'workplace': wp,
                }
            )
            if created:
                op.set_pin('1234')
                op.save()
            operators.append(op)
        users['operators'] = operators

        return users

    def _create_blanks(self, workplaces, shifts, products, users):
        """Создание бланков ПА."""
        blanks = []
        service = BlankGeneratorService()
        today = timezone.localdate()

        # Создаём бланки на сегодня, вчера и позавчера
        for day_offset in [0, -1, -2]:
            date = today + timedelta(days=day_offset)

            for wp in workplaces[:8]:  # Первые 8 РМ
                # Выбираем продукцию по типу РМ
                if 'сборк' in wp.name.lower():
                    product = products[0] if random.random() > 0.5 else products[1]
                elif 'токар' in wp.name.lower():
                    product = products[2]
                elif 'фрезер' in wp.name.lower():
                    product = products[3]
                else:
                    product = products[4]

                # Первая смена
                try:
                    blank = service.create_blank(
                        workplace=wp,
                        date=date,
                        shift=shifts[0],
                        product=product,
                        planned_quantity=int(wp.achieved_capacity * 11),  # 11 часов
                        created_by=users['masters'][0],
                    )
                    blanks.append(blank)
                except ValueError:
                    pass  # Бланк уже существует

        return blanks

    def _fill_records(self, blanks, reasons, users):
        """Заполнение записей и отклонений."""
        now = timezone.localtime()
        current_hour = now.hour

        for blank in blanks:
            records = blank.records.all().order_by('hour_number')

            # Определяем сколько часов заполнить
            if blank.date < timezone.localdate():
                # Прошлые дни - заполняем полностью
                hours_to_fill = 12
            else:
                # Сегодня - заполняем до текущего часа
                hours_to_fill = min(current_hour - 7, 12)  # смена с 8:00

            cumulative_fact = 0
            for i, record in enumerate(records[:hours_to_fill]):
                # Генерируем факт с небольшим отклонением
                deviation_factor = random.uniform(0.85, 1.1)
                actual = int(record.planned_quantity * deviation_factor)
                actual = max(0, actual)

                cumulative_fact += actual

                record.actual_quantity = actual
                record.cumulative_fact = cumulative_fact
                record.is_filled = True
                record.filled_at = timezone.now()
                record.filled_by = random.choice(users['operators'])
                record.save()

                # Добавляем отклонения для записей с низким выполнением
                if actual < record.planned_quantity * 0.9:
                    # Выбираем случайную причину
                    reason = random.choice(reasons)
                    duration = random.randint(5, 30)

                    DeviationEntry.objects.create(
                        record=record,
                        reason=reason,
                        duration_minutes=duration,
                        comment=f'Автоматически создано для демо (час {record.hour_number})',
                    )

                    # Иногда добавляем меру
                    if random.random() > 0.5:
                        deviation = record.deviations.first()
                        TakenMeasure.objects.create(
                            deviation_entry=deviation,
                            measure_type=random.choice(['fixed_onsite', 'in_repair', 'plan_adjustment']),
                            description='Мера принята в рамках демонстрации',
                            created_by=random.choice(users['masters']),
                            resolved_at=timezone.now() if random.random() > 0.3 else None,
                        )

            # Обновляем итоги бланка
            blank.recalculate_totals()

    def _print_summary(self, workshops, sectors, workplaces, users, blanks):
        """Вывод итогов."""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('ИТОГИ СОЗДАНИЯ ДЕМО-ДАННЫХ')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Цехов: {len(workshops)}')
        self.stdout.write(f'  Участков: {len(sectors)}')
        self.stdout.write(f'  Рабочих мест: {len(workplaces)}')
        self.stdout.write(f'  Смен: {Shift.objects.count()}')
        self.stdout.write(f'  Продукции: {Product.objects.count()}')
        self.stdout.write(f'  Групп причин: {DeviationGroup.objects.count()}')
        self.stdout.write(f'  Причин отклонений: {DeviationReason.objects.count()}')
        self.stdout.write(f'  Пользователей: {Employee.objects.count()}')
        self.stdout.write(f'  Бланков: {len(blanks)}')
        self.stdout.write(f'  Отклонений: {DeviationEntry.objects.count()}')
        self.stdout.write(f'  Мер: {TakenMeasure.objects.count()}')
        self.stdout.write('=' * 50)
        self.stdout.write('\nТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ:')
        self.stdout.write('-' * 50)
        self.stdout.write('  Администратор: 100000 / PIN: 0000')
        self.stdout.write('  Начальник:     200001 / PIN: 1234')
        self.stdout.write('  Мастер:        300001 / PIN: 1234')
        self.stdout.write('  Оператор:      100001 / PIN: 1234')
        self.stdout.write('=' * 50)
