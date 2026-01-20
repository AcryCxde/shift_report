import math
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db.models import (CASCADE, SET_NULL, CharField, DateField,
                              DateTimeField, DecimalField, ForeignKey, Index,
                              IntegerField, Model, PositiveIntegerField, Sum,
                              TextChoices, TextField, UniqueConstraint)


class PABlankType(TextChoices):
    """Типы бланков производственного анализа"""
    TYPE_1 = 'type_1', 'Тип 1: По времени такта'
    TYPE_2 = 'type_2', 'Тип 2: По мощности РМ'
    TYPE_3 = 'type_3', 'Тип 3: Несколько номенклатур'
    TYPE_4 = 'type_4', 'Тип 4: Менее 1 изделия в час'
    TYPE_5 = 'type_5', 'Тип 5: Менее 1 изделия в смену'


class PABlankStatus(TextChoices):
    """Статусы бланка ПА"""
    DRAFT = 'draft', 'Черновик'
    ACTIVE = 'active', 'Активен'
    COMPLETED = 'completed', 'Завершён'
    CANCELLED = 'cancelled', 'Отменён'


class PABlank(Model):
    """
    Бланк производственного анализа

    Основной документ для ведения почасового учёта выполнения плана.
    Создаётся на каждое рабочее место на каждую смену.

    Бизнес-правило BR-001: Один бланк на (РМ, дата, смена) - уникальность
    """

    class Meta:
        verbose_name = 'Бланк ПА'
        verbose_name_plural = 'Бланки ПА'
        ordering = ['-date', '-shift__number', 'workplace__number']
        constraints = [
            UniqueConstraint(
                fields=['workplace', 'date', 'shift'],
                name='unique_blank_per_workplace_date_shift'
            ),
        ]
        indexes = [
            Index(fields=['workplace', 'date', 'shift']),
            Index(fields=['date', 'status']),
            Index(fields=['created_by', 'date']),
        ]

    # Привязка к месту и времени
    workplace = ForeignKey(
        'shift_report.Workplace',
        verbose_name='Рабочее место',
        related_name='pa_blanks',
        on_delete=CASCADE,
    )

    date = DateField(
        'Дата',
    )

    shift = ForeignKey(
        'shift_report.Shift',
        verbose_name='Смена',
        related_name='pa_blanks',
        on_delete=CASCADE,
    )

    # Продукция (основная для типов 1, 2)
    product = ForeignKey(
        'shift_report.Product',
        verbose_name='Продукция',
        related_name='pa_blanks',
        on_delete=CASCADE,
    )

    # Тип и статус бланка
    blank_type = CharField(
        'Тип бланка',
        max_length=20,
        choices=PABlankType.choices,
        default=PABlankType.TYPE_1,
    )

    status = CharField(
        'Статус',
        max_length=20,
        choices=PABlankStatus.choices,
        default=PABlankStatus.DRAFT,
    )

    # Плановые показатели
    planned_quantity = PositiveIntegerField(
        'Плановый объём, шт',
        validators=[MinValueValidator(1)],
        help_text='Суточный/сменный план производства',
    )

    # Расчётные показатели (заполняются автоматически)
    takt_time = DecimalField(
        'Время такта, сек',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Тт = Фонд времени смены / Плановый объём',
    )

    production_rate = DecimalField(
        'Темп производства, шт/час',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Темп = 3600 / Тт',
    )

    hourly_plan = PositiveIntegerField(
        'Часовой план, шт',
        null=True,
        blank=True,
        help_text='План на один час (округлённый темп)',
    )

    # Для типа 2 (по мощности РМ)
    workplace_capacity = PositiveIntegerField(
        'Мощность РМ, шт/час',
        null=True,
        blank=True,
        help_text='Используется для бланков Типа 2',
    )

    # Итоговые показатели (обновляются при внесении данных)
    total_plan = PositiveIntegerField(
        'Итого план, шт',
        default=0,
        editable=False,
    )

    total_fact = PositiveIntegerField(
        'Итого факт, шт',
        default=0,
        editable=False,
    )

    total_deviation = IntegerField(
        'Итого отклонение, шт',
        default=0,
        editable=False,
        help_text='Положительное = перевыполнение, отрицательное = недовыполнение',
    )

    total_downtime = PositiveIntegerField(
        'Итого простой, мин',
        default=0,
        editable=False,
    )

    completion_percentage = DecimalField(
        'Процент выполнения, %',
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
    )

    # Примечания
    notes = TextField(
        'Примечания',
        blank=True,
        default='',
    )

    # Служебные поля
    created_by = ForeignKey(
        'shift_report.Employee',
        verbose_name='Создал',
        related_name='created_blanks',
        on_delete=SET_NULL,
        null=True,
    )

    created_at = DateTimeField(
        'Дата создания',
        auto_now_add=True,
    )

    updated_at = DateTimeField(
        'Дата обновления',
        auto_now=True,
    )

    def __str__(self):
        return f'ПА {self.workplace} | {self.date} | {self.shift}'

    def save(self, *args, **kwargs):
        # Автоматический расчёт показателей при создании
        if not self.pk:
            self._calculate_parameters()
        super().save(*args, **kwargs)

    def _calculate_parameters(self):
        """Расчёт времени такта и темпа производства"""
        if not self.shift or not self.planned_quantity:
            return

        # Фонд рабочего времени в секундах
        working_time_seconds = self.shift.working_time_minutes * 60

        # Время такта: Тт = Фонд времени / Плановый объём
        self.takt_time = Decimal(working_time_seconds) / Decimal(self.planned_quantity)

        # Темп производства: 3600 / Тт (шт/час)
        if self.takt_time > 0:
            self.production_rate = Decimal('3600') / self.takt_time

            # Часовой план (округление вверх для надёжности)
            self.hourly_plan = math.ceil(float(self.production_rate))

        # Для типа 2 берём мощность из РМ
        if self.blank_type == PABlankType.TYPE_2 and self.workplace:
            self.workplace_capacity = (
                self.workplace.passport_capacity or
                self.workplace.achieved_capacity
            )

    def recalculate_totals(self):
        """Пересчёт итоговых показателей на основе записей"""
        aggregates = self.records.aggregate(
            sum_plan=Sum('planned_quantity'),
            sum_fact=Sum('actual_quantity'),
            sum_downtime=Sum('downtime_minutes'),
        )

        self.total_plan = aggregates['sum_plan'] or 0
        self.total_fact = aggregates['sum_fact'] or 0
        self.total_deviation = self.total_fact - self.total_plan
        self.total_downtime = aggregates['sum_downtime'] or 0

        if self.total_plan > 0:
            self.completion_percentage = (
                Decimal(self.total_fact) / Decimal(self.total_plan) * 100
            )
        else:
            self.completion_percentage = Decimal('0.00')

        self.save(update_fields=[
            'total_plan', 'total_fact', 'total_deviation',
            'total_downtime', 'completion_percentage', 'updated_at'
        ])

    @property
    def is_editable(self):
        """Можно ли редактировать бланк"""
        return self.status in [PABlankStatus.DRAFT, PABlankStatus.ACTIVE]

    @property
    def current_completion_percentage(self):
        """
        Процент выполнения на текущий момент времени.

        Сравнивает фактический результат с планом за прошедшие часы,
        а не со всем планом на смену.
        """
        from django.utils import timezone

        now = timezone.localtime()
        current_time = now.time()

        # Если бланк не на сегодня, возвращаем общий процент
        if self.date != now.date():
            return self.completion_percentage

        # Находим все записи, которые уже должны были завершиться
        completed_records = self.records.filter(
            end_time__lte=current_time
        ).aggregate(
            plan=Sum('planned_quantity'),
            fact=Sum('actual_quantity')
        )

        cumulative_plan = completed_records['plan'] or 0
        cumulative_fact = completed_records['fact'] or 0

        # Если ещё не прошло ни одного часа
        if cumulative_plan == 0:
            return Decimal('0.00')

        # Процент выполнения за прошедшие часы
        current_percentage = (Decimal(cumulative_fact) / Decimal(cumulative_plan)) * 100

        return round(current_percentage, 2)

    @property
    def status_color(self):
        """Цвет статуса для UI (BR-004)"""
        percentage = self.current_completion_percentage

        if percentage >= 100:
            return 'success'  # Зелёный
        elif percentage >= 90:
            return 'warning'  # Жёлтый
        else:
            return 'danger'  # Красный