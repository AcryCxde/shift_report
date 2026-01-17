from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (CASCADE, SET_NULL, BooleanField, DateTimeField,
                              ForeignKey, Index, IntegerField, Model,
                              PositiveIntegerField, TimeField,
                              UniqueConstraint)


class PARecord(Model):
    """
    Почасовая запись производственного анализа

    Содержит плановые и фактические данные за один час смены.
    Создаётся автоматически при генерации бланка ПА.
    """

    class Meta:
        verbose_name = 'Запись ПА'
        verbose_name_plural = 'Записи ПА'
        ordering = ['blank', 'hour_number']
        constraints = [
            UniqueConstraint(
                fields=['blank', 'hour_number'],
                name='unique_record_per_blank_hour'
            ),
        ]
        indexes = [
            Index(fields=['blank', 'hour_number']),
            Index(fields=['is_filled']),
        ]

    blank = ForeignKey(
        'shift_report.PABlank',
        verbose_name='Бланк ПА',
        related_name='records',
        on_delete=CASCADE,
    )

    # Номер часа в смене (1, 2, 3, ...)
    hour_number = PositiveIntegerField(
        'Номер часа',
        validators=[MinValueValidator(1), MaxValueValidator(24)],
    )

    # Время интервала
    start_time = TimeField(
        'Время начала',
    )

    end_time = TimeField(
        'Время окончания',
    )

    # Плановые показатели (заполняются при создании бланка)
    planned_quantity = PositiveIntegerField(
        'План, шт',
        default=0,
    )

    cumulative_plan = PositiveIntegerField(
        'План накопительный, шт',
        default=0,
        help_text='Сумма плана с начала смены',
    )

    # Фактические показатели (заполняются оператором)
    actual_quantity = PositiveIntegerField(
        'Факт, шт',
        default=0,
    )

    cumulative_fact = PositiveIntegerField(
        'Факт накопительный, шт',
        default=0,
        help_text='Сумма факта с начала смены',
    )

    # Отклонения (рассчитываются автоматически)
    deviation = IntegerField(
        'Отклонение, шт',
        default=0,
        help_text='Факт - План (может быть отрицательным)',
    )

    cumulative_deviation = IntegerField(
        'Отклонение накопительное, шт',
        default=0,
    )

    # Простои
    downtime_minutes = PositiveIntegerField(
        'Простой, мин',
        default=0,
    )

    # Статус заполнения
    is_filled = BooleanField(
        'Заполнено',
        default=False,
        help_text='Отмечается при внесении фактических данных',
    )

    filled_at = DateTimeField(
        'Время заполнения',
        null=True,
        blank=True,
    )

    filled_by = ForeignKey(
        'shift_report.Employee',
        verbose_name='Заполнил',
        related_name='filled_records',
        on_delete=SET_NULL,
        null=True,
        blank=True,
    )

    # Служебные поля
    created_at = DateTimeField(
        'Дата создания',
        auto_now_add=True,
    )

    updated_at = DateTimeField(
        'Дата обновления',
        auto_now=True,
    )

    def __str__(self):
        return f'{self.blank} | Час {self.hour_number}'

    def save(self, *args, **kwargs):
        # Автоматический расчёт отклонения
        self.deviation = self.actual_quantity - self.planned_quantity
        super().save(*args, **kwargs)

    def calculate_cumulative(self):
        """
        Пересчёт накопительных показателей.
        Вызывается после обновления записи.
        """
        # Получаем все записи до текущей включительно
        previous_records = self.blank.records.filter(
            hour_number__lte=self.hour_number
        ).order_by('hour_number')

        cumulative_plan = 0
        cumulative_fact = 0

        for record in previous_records:
            cumulative_plan += record.planned_quantity
            cumulative_fact += record.actual_quantity

            if record.pk == self.pk:
                self.cumulative_plan = cumulative_plan
                self.cumulative_fact = cumulative_fact
                self.cumulative_deviation = cumulative_fact - cumulative_plan
            else:
                # Обновляем предыдущие записи если нужно
                if (record.cumulative_plan != cumulative_plan or
                        record.cumulative_fact != cumulative_fact):
                    record.cumulative_plan = cumulative_plan
                    record.cumulative_fact = cumulative_fact
                    record.cumulative_deviation = cumulative_fact - cumulative_plan
                    record.save(update_fields=[
                        'cumulative_plan', 'cumulative_fact',
                        'cumulative_deviation', 'updated_at'
                    ])

    @property
    def status_color(self):
        """Цвет статуса для UI (BR-004)"""
        if not self.is_filled:
            return 'secondary'  # Серый - не заполнено
        if self.actual_quantity >= self.planned_quantity:
            return 'success'  # Зелёный
        elif self.actual_quantity >= self.planned_quantity * Decimal('0.9'):
            return 'warning'  # Жёлтый
        else:
            return 'danger'  # Красный

    @property
    def completion_percentage(self):
        """Процент выполнения за час"""
        if self.planned_quantity > 0:
            return (self.actual_quantity / self.planned_quantity) * 100
        return 0
