from django.db.models import (CASCADE, BooleanField, CharField, ForeignKey,
                              Model, PositiveIntegerField, TextField)


class Workplace(Model):
    """
    Рабочее место (РМ)

    Нижний уровень иерархии подразделений.
    На рабочем месте ведётся производственный анализ.
    """

    class Meta:
        verbose_name = 'Рабочее место'
        verbose_name_plural = 'Рабочие места'
        ordering = ['sector__workshop__number', 'sector__number', 'number']
        unique_together = [['sector', 'number']]

    sector = ForeignKey(
        'shift_report.Sector',
        verbose_name='Участок',
        related_name='workplaces',
        on_delete=CASCADE,
    )

    number = PositiveIntegerField(
        'Номер рабочего места',
    )

    name = CharField(
        'Название рабочего места',
        max_length=255,
    )

    equipment_type = CharField(
        'Тип оборудования',
        max_length=255,
        blank=True,
        default='',
    )

    passport_capacity = PositiveIntegerField(
        'Паспортная мощность, шт/час',
        null=True,
        blank=True,
        help_text='Используется для бланков Типа 2 (по мощности РМ)',
    )

    achieved_capacity = PositiveIntegerField(
        'Достигнутая мощность, шт/час',
        null=True,
        blank=True,
        help_text='Статистическая мощность на основе фактических данных',
    )

    description = TextField(
        'Описание',
        blank=True,
        default='',
    )

    is_active = BooleanField(
        'Активно',
        default=True,
    )

    def __str__(self):
        return f'РМ №{self.number} - {self.name} ({self.sector})'

    @property
    def full_path(self):
        """Полный путь: Цех → Участок → РМ"""
        return f'{self.sector.workshop} → {self.sector} → {self}'
