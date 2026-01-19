"""
Сервис импорта и экспорта данных.

FR-030: Импорт справочников из Excel
FR-031: Экспорт данных
"""

import csv
import io
from datetime import datetime
from typing import Any

from django.db import transaction

from shift_report.models import (DeviationEntry, DeviationGroup,
                                 DeviationReason, Employee, PABlank, Product,
                                 Sector, Shift, Workplace, Workshop)


class ImportExportService:
    """
    Сервис для импорта и экспорта данных.
    """

    # Маппинг моделей для импорта
    MODEL_MAPPING = {
        'workshops': Workshop,
        'sectors': Sector,
        'workplaces': Workplace,
        'products': Product,
        'shifts': Shift,
        'deviation_groups': DeviationGroup,
        'deviation_reasons': DeviationReason,
        'employees': Employee,
    }

    def import_from_csv(
        self,
        model_name: str,
        csv_content: str,
        update_existing: bool = False,
    ) -> dict[str, Any]:
        """
        Импорт данных из CSV.
        """
        if model_name not in self.MODEL_MAPPING:
            return {'created': 0, 'updated': 0, 'errors': [f'Неизвестная модель: {model_name}']}

        model_class = self.MODEL_MAPPING[model_name]

        created = 0
        updated = 0
        errors = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))

            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    try:
                        result = self._import_row(model_class, model_name, row, update_existing)
                        if result == 'created':
                            created += 1
                        elif result == 'updated':
                            updated += 1
                    except Exception as e:
                        errors.append(f'Строка {row_num}: {str(e)}')

        except Exception as e:
            errors.append(f'Ошибка чтения CSV: {str(e)}')

        return {
            'created': created,
            'updated': updated,
            'errors': errors,
        }

    def _import_row(
        self,
        model_class,
        model_name: str,
        row: dict,
        update_existing: bool,
    ) -> str:
        """
        Импорт одной строки.
        """
        if model_name == 'workshops':
            return self._import_workshop(row, update_existing)
        elif model_name == 'sectors':
            return self._import_sector(row, update_existing)
        elif model_name == 'workplaces':
            return self._import_workplace(row, update_existing)
        elif model_name == 'products':
            return self._import_product(row, update_existing)
        elif model_name == 'shifts':
            return self._import_shift(row, update_existing)
        elif model_name == 'deviation_groups':
            return self._import_deviation_group(row, update_existing)
        elif model_name == 'deviation_reasons':
            return self._import_deviation_reason(row, update_existing)
        elif model_name == 'employees':
            return self._import_employee(row, update_existing)

        return 'skipped'

    def _import_workshop(self, row: dict, update_existing: bool) -> str:
        number = int(row.get('number', 0))
        if not number:
            raise ValueError('Не указан номер цеха')

        defaults = {
            'name': row.get('name', '').strip(),
            'description': row.get('description', '').strip(),
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = Workshop.objects.update_or_create(number=number, defaults=defaults)
        else:
            obj, created = Workshop.objects.get_or_create(number=number, defaults=defaults)

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_sector(self, row: dict, update_existing: bool) -> str:
        number = int(row.get('number', 0))
        workshop_number = int(row.get('workshop_number', 0))

        if not number or not workshop_number:
            raise ValueError('Не указан номер участка или цеха')

        workshop = Workshop.objects.get(number=workshop_number)

        defaults = {
            'name': row.get('name', '').strip(),
            'description': row.get('description', '').strip(),
            'workshop': workshop,
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = Sector.objects.update_or_create(
                workshop=workshop, number=number, defaults=defaults
            )
        else:
            obj, created = Sector.objects.get_or_create(
                workshop=workshop, number=number, defaults=defaults
            )

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_workplace(self, row: dict, update_existing: bool) -> str:
        number = int(row.get('number', 0))
        sector_number = int(row.get('sector_number', 0))
        workshop_number = int(row.get('workshop_number', 0))

        if not number or not sector_number:
            raise ValueError('Не указан номер РМ или участка')

        sector = Sector.objects.get(number=sector_number, workshop__number=workshop_number)

        defaults = {
            'name': row.get('name', '').strip(),
            'description': row.get('description', '').strip(),
            'sector': sector,
            'equipment_type': row.get('equipment_type', '').strip() or None,
            'passport_capacity': float(row.get('passport_capacity', 0)) or None,
            'achieved_capacity': float(row.get('achieved_capacity', 0)) or None,
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = Workplace.objects.update_or_create(
                sector=sector, number=number, defaults=defaults
            )
        else:
            obj, created = Workplace.objects.get_or_create(
                sector=sector, number=number, defaults=defaults
            )

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_product(self, row: dict, update_existing: bool) -> str:
        article = row.get('article', '').strip()
        if not article:
            raise ValueError('Не указан артикул')

        defaults = {
            'name': row.get('name', '').strip(),
            'takt_time': int(row.get('takt_time', 0)) or None,
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = Product.objects.update_or_create(article=article, defaults=defaults)
        else:
            obj, created = Product.objects.get_or_create(article=article, defaults=defaults)

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_shift(self, row: dict, update_existing: bool) -> str:
        number = int(row.get('number', 0))
        if not number:
            raise ValueError('Не указан номер смены')

        defaults = {
            'name': row.get('name', '').strip(),
            'start_time': datetime.strptime(row.get('start_time', '08:00'), '%H:%M').time(),
            'end_time': datetime.strptime(row.get('end_time', '20:00'), '%H:%M').time(),
            'break_minutes': int(row.get('break_minutes', 60)),
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = Shift.objects.update_or_create(number=number, defaults=defaults)
        else:
            obj, created = Shift.objects.get_or_create(number=number, defaults=defaults)

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_deviation_group(self, row: dict, update_existing: bool) -> str:
        code = row.get('code', '').strip()
        if not code:
            raise ValueError('Не указан код группы')

        defaults = {
            'name': row.get('name', '').strip(),
            'color': row.get('color', '#6c757d').strip(),
            'order': int(row.get('order', 0)),
        }

        if update_existing:
            obj, created = DeviationGroup.objects.update_or_create(code=code, defaults=defaults)
        else:
            obj, created = DeviationGroup.objects.get_or_create(code=code, defaults=defaults)

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_deviation_reason(self, row: dict, update_existing: bool) -> str:
        code = row.get('code', '').strip()
        group_code = row.get('group_code', '').strip()

        if not code or not group_code:
            raise ValueError('Не указан код причины или группы')

        group = DeviationGroup.objects.get(code=group_code)

        defaults = {
            'name': row.get('name', '').strip(),
            'group': group,
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = DeviationReason.objects.update_or_create(code=code, defaults=defaults)
        else:
            obj, created = DeviationReason.objects.get_or_create(code=code, defaults=defaults)

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def _import_employee(self, row: dict, update_existing: bool) -> str:
        personnel_number = row.get('personnel_number', '').strip()
        if not personnel_number:
            raise ValueError('Не указан табельный номер')

        # Находим связанные объекты
        workshop = None
        sector = None
        workplace = None

        if row.get('workshop_number'):
            workshop = Workshop.objects.get(number=int(row['workshop_number']))
        if row.get('sector_number') and row.get('workshop_number'):
            sector = Sector.objects.get(
                number=int(row['sector_number']),
                workshop__number=int(row['workshop_number'])
            )
        if row.get('workplace_number') and sector:
            workplace = Workplace.objects.get(
                number=int(row['workplace_number']),
                sector=sector
            )

        defaults = {
            'first_name': row.get('first_name', '').strip(),
            'last_name': row.get('last_name', '').strip(),
            'middle_name': row.get('middle_name', '').strip() or None,
            'role': row.get('role', 'operator').strip(),
            'workshop': workshop,
            'sector': sector,
            'workplace': workplace,
            'is_active': row.get('is_active', 'true').lower() == 'true',
        }

        if update_existing:
            obj, created = Employee.objects.update_or_create(
                personnel_number=personnel_number,
                defaults=defaults
            )
        else:
            obj, created = Employee.objects.get_or_create(
                personnel_number=personnel_number,
                defaults=defaults
            )

        # Устанавливаем PIN если указан
        if created and row.get('pin'):
            obj.set_pin(row['pin'].strip())
            obj.save()

        return 'created' if created else ('updated' if update_existing else 'skipped')

    def export_to_csv(
        self,
        model_name: str,
        filters: dict = None,
    ) -> str:
        """
        Экспорт данных в CSV.
        """
        if model_name not in self.MODEL_MAPPING:
            raise ValueError(f'Неизвестная модель: {model_name}')

        model_class = self.MODEL_MAPPING[model_name]
        queryset = model_class.objects.all()

        if filters:
            queryset = queryset.filter(**filters)

        output = io.StringIO()

        if model_name == 'workshops':
            self._export_workshops(queryset, output)
        elif model_name == 'sectors':
            self._export_sectors(queryset, output)
        elif model_name == 'workplaces':
            self._export_workplaces(queryset, output)
        elif model_name == 'products':
            self._export_products(queryset, output)
        elif model_name == 'shifts':
            self._export_shifts(queryset, output)
        elif model_name == 'deviation_groups':
            self._export_deviation_groups(queryset, output)
        elif model_name == 'deviation_reasons':
            self._export_deviation_reasons(queryset, output)
        elif model_name == 'employees':
            self._export_employees(queryset, output)

        return output.getvalue()

    def _export_workshops(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['number', 'name', 'description', 'is_active'])
        for obj in queryset:
            writer.writerow([obj.number, obj.name, obj.description, obj.is_active])

    def _export_sectors(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['number', 'name', 'workshop_number', 'description', 'is_active'])
        for obj in queryset.select_related('workshop'):
            writer.writerow([obj.number, obj.name, obj.workshop.number, obj.description, obj.is_active])

    def _export_workplaces(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow([
                'number',
                'name',
                'sector_number',
                'workshop_number',
                'equipment_type',
                'passport_capacity',
                'achieved_capacity',
                'description',
                'is_active'
                ])
        for obj in queryset.select_related('sector', 'sector__workshop'):
            writer.writerow([
                obj.number, obj.name, obj.sector.number, obj.sector.workshop.number,
                obj.equipment_type or '', obj.passport_capacity or '',
                obj.achieved_capacity or '', obj.description, obj.is_active
            ])

    def _export_products(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['article', 'name', 'takt_time', 'is_active'])
        for obj in queryset:
            writer.writerow([obj.article, obj.name, obj.takt_time or '', obj.is_active])

    def _export_shifts(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['number', 'name', 'start_time', 'end_time', 'break_minutes', 'is_active'])
        for obj in queryset:
            writer.writerow([
                obj.number, obj.name,
                obj.start_time.strftime('%H:%M'), obj.end_time.strftime('%H:%M'),
                obj.break_minutes, obj.is_active
            ])

    def _export_deviation_groups(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['code', 'name', 'color', 'order'])
        for obj in queryset:
            writer.writerow([obj.code, obj.name, obj.color, obj.order])

    def _export_deviation_reasons(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['code', 'name', 'group_code', 'is_active'])
        for obj in queryset.select_related('group'):
            writer.writerow([obj.code, obj.name, obj.group.code, obj.is_active])

    def _export_employees(self, queryset, output):
        writer = csv.writer(output)
        writer.writerow(['personnel_number', 'first_name', 'last_name', 'middle_name',
                        'role', 'workshop_number', 'sector_number', 'workplace_number', 'is_active'])
        for obj in queryset.select_related('workshop', 'sector', 'workplace'):
            writer.writerow([
                obj.personnel_number, obj.first_name, obj.last_name, obj.middle_name or '',
                obj.role,
                obj.workshop.number if obj.workshop else '',
                obj.sector.number if obj.sector else '',
                obj.workplace.number if obj.workplace else '',
                obj.is_active
            ])

    def export_blanks_report(
        self,
        date_from,
        date_to,
        workshop=None,
        sector=None,
    ) -> str:
        """
        Экспорт отчёта по бланкам.
        """
        blanks = PABlank.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        ).select_related(
            'workplace',
            'workplace__sector',
            'product',
            'shift',
        ).order_by('date', 'shift__number', 'workplace__number')

        if sector:
            blanks = blanks.filter(workplace__sector=sector)
        elif workshop:
            blanks = blanks.filter(workplace__sector__workshop=workshop)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Дата', 'Смена', 'Участок', 'Рабочее место', 'Продукция',
            'План', 'Факт', 'Отклонение', 'Выполнение %', 'Простои (мин)', 'Статус'
        ])

        for blank in blanks:
            writer.writerow([
                blank.date.strftime('%d.%m.%Y'),
                blank.shift.name,
                blank.workplace.sector.name,
                blank.workplace.name,
                blank.product.article,
                blank.total_plan,
                blank.total_fact,
                blank.total_deviation,
                f'{blank.completion_percentage:.1f}',
                blank.total_downtime,
                blank.get_status_display(),
            ])

        return output.getvalue()

    def export_deviations_report(
        self,
        date_from,
        date_to,
        workshop=None,
        sector=None,
    ) -> str:
        """
        Экспорт отчёта по отклонениям.
        """
        deviations = DeviationEntry.objects.filter(
            record__blank__date__gte=date_from,
            record__blank__date__lte=date_to,
        ).select_related(
            'record',
            'record__blank',
            'record__blank__workplace',
            'record__blank__workplace__sector',
            'reason',
            'reason__group',
        ).order_by('record__blank__date', 'record__hour_number')

        if sector:
            deviations = deviations.filter(record__blank__workplace__sector=sector)
        elif workshop:
            deviations = deviations.filter(record__blank__workplace__sector__workshop=workshop)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Дата', 'Час', 'Участок', 'Рабочее место',
            'Группа причины', 'Причина', 'Длительность (мин)', 'Комментарий'
        ])

        for dev in deviations:
            writer.writerow([
                dev.record.blank.date.strftime('%d.%m.%Y'),
                dev.record.hour_number,
                dev.record.blank.workplace.sector.name,
                dev.record.blank.workplace.name,
                dev.reason.group.name,
                dev.reason.name,
                dev.duration_minutes or '',
                dev.comment or '',
            ])

        return output.getvalue()
