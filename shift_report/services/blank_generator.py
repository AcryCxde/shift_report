"""
Сервис генерации бланков производственного анализа.

Реализует FR-007: Автоматическая генерация бланков ПА с расчётами.
"""

import math
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction

from shift_report.models import (PABlank, PABlankStatus, PABlankType, PARecord,
                                 PATemplate, Product, Shift, Workplace)


class BlankGeneratorService:
    """
    Сервис для создания бланков ПА с автоматическим расчётом параметров.

    Основные функции:
    - Расчёт времени такта и темпа производства
    - Определение типа бланка (1 или 2)
    - Генерация почасовых интервалов
    - Создание бланков из шаблонов
    """

    def create_blank(
        self,
        workplace: Workplace,
        date,
        shift: Shift,
        product: Product,
        planned_quantity: int,
        blank_type: str = None,
        created_by=None,
    ) -> PABlank:
        """
        Создаёт бланк ПА с автоматической генерацией записей.

        Args:
            workplace: Рабочее место
            date: Дата бланка
            shift: Смена
            product: Продукция
            planned_quantity: Плановый объём на смену
            blank_type: Тип бланка (если не указан, определяется автоматически)
            created_by: Сотрудник, создающий бланк

        Returns:
            PABlank: Созданный бланк с записями

        Raises:
            ValueError: Если бланк уже существует или параметры невалидны
        """
        # Проверка уникальности (BR-001)
        if PABlank.objects.filter(
            workplace=workplace,
            date=date,
            shift=shift
        ).exists():
            raise ValueError(
                f'Бланк для РМ {workplace}, дата {date}, смена {shift} уже существует'
            )

        # Определение типа бланка (BR-007)
        if blank_type is None:
            blank_type = self._determine_blank_type(
                workplace, shift, planned_quantity
            )

        with transaction.atomic():
            # Создание бланка
            blank = PABlank.objects.create(
                workplace=workplace,
                date=date,
                shift=shift,
                product=product,
                blank_type=blank_type,
                planned_quantity=planned_quantity,
                status=PABlankStatus.ACTIVE,
                created_by=created_by,
            )

            # Генерация почасовых записей
            self._generate_records(blank)

            # Пересчёт итогов
            blank.recalculate_totals()

        return blank

    def create_from_template(
        self,
        template: PATemplate,
        date,
        shift: Shift = None,
        created_by=None,
    ) -> PABlank:
        """
        Создаёт бланк ПА на основе шаблона.

        Args:
            template: Шаблон бланка
            date: Дата бланка
            shift: Смена (если не указана, берётся из шаблона)
            created_by: Сотрудник, создающий бланк

        Returns:
            PABlank: Созданный бланк
        """
        return self.create_blank(
            workplace=template.workplace,
            date=date,
            shift=shift or template.shift,
            product=template.product,
            planned_quantity=template.planned_quantity,
            blank_type=template.blank_type,
            created_by=created_by,
        )

    def create_blanks_for_sector(
        self,
        sector,
        date,
        shift: Shift,
        created_by=None,
    ) -> list[PABlank]:
        """
        Массовое создание бланков для всех РМ участка.

        Args:
            sector: Участок
            date: Дата
            shift: Смена
            created_by: Сотрудник

        Returns:
            list[PABlank]: Список созданных бланков
        """
        blanks = []
        workplaces = sector.workplaces.filter(is_active=True)

        for workplace in workplaces:
            # Ищем подходящий шаблон
            template = PATemplate.objects.filter(
                workplace=workplace,
                is_active=True,
            ).first()

            if template:
                # Проверяем применимость по дню недели
                weekday = date.weekday()
                if template.is_applicable_for_weekday(weekday):
                    try:
                        blank = self.create_from_template(
                            template=template,
                            date=date,
                            shift=shift,
                            created_by=created_by,
                        )
                        blanks.append(blank)
                    except ValueError:
                        # Бланк уже существует, пропускаем
                        pass

        return blanks

    def _determine_blank_type(
        self,
        workplace: Workplace,
        shift: Shift,
        planned_quantity: int,
    ) -> str:
        """
        Автоматическое определение типа бланка (BR-007).

        Логика:
        - Тип 1: Темп > 1 шт/час, однородное производство
        - Тип 2: Темп > 1 шт/час, есть паспортная мощность РМ

        Args:
            workplace: Рабочее место
            shift: Смена
            planned_quantity: Плановый объём

        Returns:
            str: Тип бланка (PABlankType)
        """
        # Расчёт темпа производства
        working_time_seconds = shift.working_time_minutes * 60
        takt_time = Decimal(working_time_seconds) / Decimal(planned_quantity)
        production_rate = Decimal('3600') / takt_time if takt_time > 0 else 0  # noqa: F841

        # Если есть паспортная мощность РМ → Тип 2
        if workplace.passport_capacity or workplace.achieved_capacity:
            return PABlankType.TYPE_2

        # Иначе → Тип 1
        return PABlankType.TYPE_1

    def _generate_records(self, blank: PABlank) -> list[PARecord]:
        """
        Генерация почасовых записей для бланка.

        Разбивает смену на часовые интервалы и создаёт PARecord для каждого.

        Args:
            blank: Бланк ПА

        Returns:
            list[PARecord]: Список созданных записей
        """
        records = []
        shift = blank.shift

        # Расчёт количества часов в смене
        working_hours = shift.working_time_minutes // 60
        remaining_minutes = shift.working_time_minutes % 60

        # Расчёт плана на час
        hourly_plan = blank.hourly_plan or math.ceil(
            float(blank.production_rate or 0)
        )

        # Генерация интервалов
        current_time = datetime.combine(blank.date, shift.start_time)
        cumulative_plan = 0

        for hour_number in range(1, working_hours + 2):  # +1 для учёта неполного часа
            # Расчёт времени интервала
            start_time = current_time.time()

            # Определяем длительность интервала
            if hour_number <= working_hours:
                interval_minutes = 60
            elif remaining_minutes > 0:
                interval_minutes = remaining_minutes
            else:
                break

            current_time += timedelta(minutes=interval_minutes)
            end_time = current_time.time()

            # Расчёт плана для этого интервала
            if hour_number <= working_hours:
                plan_for_hour = hourly_plan
            else:
                # Для неполного часа пропорционально уменьшаем план
                plan_for_hour = math.ceil(hourly_plan * remaining_minutes / 60)

            cumulative_plan += plan_for_hour

            # Создание записи
            record = PARecord.objects.create(
                blank=blank,
                hour_number=hour_number,
                start_time=start_time,
                end_time=end_time,
                planned_quantity=plan_for_hour,
                cumulative_plan=cumulative_plan,
            )
            records.append(record)

        return records

    def recalculate_blank(self, blank: PABlank) -> None:
        """
        Пересчёт всех накопительных показателей бланка.

        Вызывается после обновления записей.
        """
        records = blank.records.order_by('hour_number')

        cumulative_plan = 0
        cumulative_fact = 0

        for record in records:
            cumulative_plan += record.planned_quantity
            cumulative_fact += record.actual_quantity

            record.cumulative_plan = cumulative_plan
            record.cumulative_fact = cumulative_fact
            record.cumulative_deviation = cumulative_fact - cumulative_plan
            record.deviation = record.actual_quantity - record.planned_quantity
            record.save(update_fields=[
                'cumulative_plan', 'cumulative_fact',
                'cumulative_deviation', 'deviation', 'updated_at'
            ])

        # Обновляем итоги бланка
        blank.recalculate_totals()
