from django.db.models import (CASCADE, BooleanField, CharField, ForeignKey,
                              Model, PositiveIntegerField, TextField)


class Sector(Model):
    """
    Участок

    Средний уровень иерархии подразделений.
    Участок принадлежит цеху и содержит рабочие места (Workplace).
    """

    class Meta:
        verbose_name = 'Участок'
        verbose_name_plural = 'Участки'
        ordering = ['workshop__number', 'number']
        unique_together = [['workshop', 'number']]

    workshop = ForeignKey(
        'shift_report.Workshop',
        verbose_name='Цех',
        related_name='sectors',
        on_delete=CASCADE,
    )

    number = PositiveIntegerField(
        'Номер участка',
    )

    name = CharField(
        'Название участка',
        max_length=255,
    )

    description = TextField(
        'Описание',
        blank=True,
        default='',
    )

    is_active = BooleanField(
        'Активен',
        default=True,
    )

    def __str__(self):
        return f'Участок №{self.number} ({self.workshop})'
