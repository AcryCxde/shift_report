from django.db.models import (CASCADE, SET_NULL, DateTimeField, ForeignKey,
                              Index, Model, PositiveIntegerField, TextField)


class DeviationEntry(Model):
    """
    Запись об отклонении (простое)

    Фиксирует причину отклонения для конкретной почасовой записи.
    Одна запись PARecord может иметь несколько DeviationEntry
    (если было несколько причин простоя за час).

    Бизнес-правило BR-003: Обязательность указания причины при отклонении
    """

    class Meta:
        verbose_name = 'Запись об отклонении'
        verbose_name_plural = 'Записи об отклонениях'
        ordering = ['-created_at']
        indexes = [
            Index(fields=['record', 'reason']),
            Index(fields=['reason']),
            Index(fields=['created_at']),
        ]

    record = ForeignKey(
        'shift_report.PARecord',
        verbose_name='Запись ПА',
        related_name='deviations',
        on_delete=CASCADE,
    )

    reason = ForeignKey(
        'shift_report.DeviationReason',
        verbose_name='Причина отклонения',
        related_name='deviation_entries',
        on_delete=CASCADE,
    )

    # Длительность простоя по этой причине
    duration_minutes = PositiveIntegerField(
        'Длительность, мин',
        default=0,
        help_text='Время простоя по данной причине',
    )

    # Ответственный за простой (опционально)
    responsible = ForeignKey(
        'shift_report.Employee',
        verbose_name='Ответственный за простой',
        related_name='responsible_for_deviations',
        on_delete=SET_NULL,
        null=True,
        blank=True,
    )

    # Комментарий оператора
    comment = TextField(
        'Комментарий',
        blank=True,
        default='',
        help_text='Дополнительные пояснения к причине отклонения',
    )

    # Кто зафиксировал
    created_by = ForeignKey(
        'shift_report.Employee',
        verbose_name='Создал',
        related_name='created_deviations',
        on_delete=SET_NULL,
        null=True,
    )

    created_at = DateTimeField(
        'Дата создания',
        auto_now_add=True,
    )

    def __str__(self):
        return f'{self.record} | {self.reason.name} ({self.duration_minutes} мин)'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Обновляем счётчик использования причины (для топ-5)
        self._update_reason_usage_count()

    def _update_reason_usage_count(self):
        """Обновление статистики использования причины"""
        count = DeviationEntry.objects.filter(reason=self.reason).count()
        self.reason.usage_count = count
        self.reason.save(update_fields=['usage_count'])
