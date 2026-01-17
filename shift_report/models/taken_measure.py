from django.db.models import (CASCADE, SET_NULL, CharField, DateTimeField,
                              ForeignKey, Index, Model, TextChoices, TextField)


class MeasureType(TextChoices):
    """Типы принятых мер"""
    FIXED = 'fixed', 'Устранено'
    IN_REPAIR = 'in_repair', 'В ремонте'
    OPERATOR_REPLACED = 'operator_replaced', 'Заменён оператор'
    PLAN_ADJUSTED = 'plan_adjusted', 'Скорректирован план'
    ESCALATED = 'escalated', 'Эскалировано'
    OTHER = 'other', 'Другое'


class TakenMeasure(Model):
    """
    Принятая мера

    Документирует действия мастера по устранению проблемы.
    Привязывается к конкретному отклонению (DeviationEntry).

    FR-025: Фиксация принятых мер
    """

    class Meta:
        verbose_name = 'Принятая мера'
        verbose_name_plural = 'Принятые меры'
        ordering = ['-created_at']
        indexes = [
            Index(fields=['deviation_entry']),
            Index(fields=['measure_type']),
            Index(fields=['created_at']),
        ]

    deviation_entry = ForeignKey(
        'shift_report.DeviationEntry',
        verbose_name='Отклонение',
        related_name='measures',
        on_delete=CASCADE,
    )

    measure_type = CharField(
        'Тип меры',
        max_length=30,
        choices=MeasureType.choices,
        default=MeasureType.OTHER,
    )

    description = TextField(
        'Описание меры',
        help_text='Подробное описание принятых действий',
    )

    # Время устранения проблемы
    resolved_at = DateTimeField(
        'Время устранения',
        null=True,
        blank=True,
        help_text='Когда проблема была устранена',
    )

    # Кто принял меру (мастер)
    created_by = ForeignKey(
        'shift_report.Employee',
        verbose_name='Принял меру',
        related_name='taken_measures',
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
        return f'{self.get_measure_type_display()}: {self.description[:50]}'

    @property
    def is_resolved(self):
        """Проблема устранена?"""
        return self.resolved_at is not None
