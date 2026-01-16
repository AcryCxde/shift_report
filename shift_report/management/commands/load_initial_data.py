"""
Management command to load initial reference data.

Usage:
    python manage.py load_initial_data
"""

from django.core.management.base import BaseCommand

from shift_report.models import DeviationGroup, DeviationReason, Shift


class Command(BaseCommand):
    help = 'Загрузка начальных справочных данных (смены, причины отклонений)'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка начальных данных...')

        self._create_shifts()
        self._create_deviation_groups()

        self.stdout.write(
            self.style.SUCCESS('Начальные данные успешно загружены!')
        )

    def _create_shifts(self):
        """Создание базовых смен"""
        shifts_data = [
            {
                'number': 1,
                'name': 'Первая смена',
                'start_time': '08:00',
                'end_time': '16:00',
                'lunch_break': 30,
                'personal_break': 10,
                'handover_break': 10,
            },
            {
                'number': 2,
                'name': 'Вторая смена',
                'start_time': '16:00',
                'end_time': '00:00',
                'lunch_break': 30,
                'personal_break': 10,
                'handover_break': 10,
            },
            {
                'number': 3,
                'name': 'Третья смена',
                'start_time': '00:00',
                'end_time': '08:00',
                'lunch_break': 30,
                'personal_break': 10,
                'handover_break': 10,
            },
        ]

        for shift_data in shifts_data:
            shift, created = Shift.objects.get_or_create(
                number=shift_data['number'],
                defaults=shift_data
            )
            # if created:
            #     self.stdout.write(f'  Создана смена: {shift}')
            # else:
            #     self.stdout.write(f'  Смена уже существует: {shift}')

    def _create_deviation_groups(self):
        """Создание групп причин отклонений по методологии МУ-55-2024"""
        groups_data = [
            {
                'code': 'ORG',
                'name': 'Организационные',
                'color': '#fd7e14',  # orange
                'order': 1,
                'reasons': [
                    ('ORG-01', 'Отсутствие работника', 1),
                    ('ORG-02', 'Опоздание работника', 2),
                    ('ORG-03', 'Неопытность работника', 3),
                    ('ORG-04', 'Отсутствие задания', 4),
                    ('ORG-05', 'Ожидание указаний', 5),
                    ('ORG-06', 'Совещание/обучение', 6),
                ],
            },
            {
                'code': 'TECH',
                'name': 'Технические',
                'color': '#dc3545',  # red
                'order': 2,
                'reasons': [
                    ('TECH-01', 'Поломка оборудования', 1),
                    ('TECH-02', 'Поломка инструмента', 2),
                    ('TECH-03', 'Отсутствие энергоносителей', 3),
                    ('TECH-04', 'Настройка/переналадка', 4),
                    ('TECH-05', 'Плановое ТО', 5),
                ],
            },
            {
                'code': 'SUPPLY',
                'name': 'Нет поставок',
                'color': '#6f42c1',  # purple
                'order': 3,
                'reasons': [
                    ('SUPPLY-01', 'Нет заготовок', 1),
                    ('SUPPLY-02', 'Нет комплектующих', 2),
                    ('SUPPLY-03', 'Нет инструмента', 3),
                    ('SUPPLY-04', 'Нет расходных материалов', 4),
                    ('SUPPLY-05', 'Нет тары', 5),
                ],
            },
            {
                'code': 'MAINT',
                'name': 'Регламентные работы',
                'color': '#20c997',  # teal
                'order': 4,
                'reasons': [
                    ('MAINT-01', 'Уборка рабочего места', 1),
                    ('MAINT-02', 'Контроль качества', 2),
                    ('MAINT-03', 'Документирование', 3),
                ],
            },
            {
                'code': 'QUALITY',
                'name': 'Качество',
                'color': '#0d6efd',  # blue
                'order': 5,
                'reasons': [
                    ('QUALITY-01', 'Брак материала', 1),
                    ('QUALITY-02', 'Брак обработки', 2),
                    ('QUALITY-03', 'Переделка', 3),
                    ('QUALITY-04', 'Доработка', 4),
                ],
            },
            {
                'code': 'OTHER',
                'name': 'Прочее',
                'color': '#6c757d',  # gray
                'order': 6,
                'reasons': [
                    ('OTHER-01', 'Прочие причины', 1),
                ],
            },
        ]

        for group_data in groups_data:
            reasons = group_data.pop('reasons')

            group, created = DeviationGroup.objects.get_or_create(
                code=group_data['code'],
                defaults=group_data
            )
            if created:
                self.stdout.write(f'  Создана группа: {group}')
            else:
                self.stdout.write(f'  Группа уже существует: {group}')

            for reason_code, reason_name, reason_order in reasons:
                reason, created = DeviationReason.objects.get_or_create(
                    code=reason_code,
                    defaults={
                        'group': group,
                        'name': reason_name,
                        'order': reason_order,
                    }
                )
                if created:
                    self.stdout.write(f'    Создана причина: {reason}')
