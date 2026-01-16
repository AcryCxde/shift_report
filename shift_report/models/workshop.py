from django.db.models import (BooleanField, CharField, Model,
                              PositiveIntegerField, TextField)


class Workshop(Model):
    """
    Цех

    Верхний уровень иерархии подразделений.
    Цех содержит участки (Sector).
    """

    class Meta:
        verbose_name = 'Цех'
        verbose_name_plural = 'Цеха'
        ordering = ['number']

    number = PositiveIntegerField(
        'Номер цеха',
        unique=True,
    )

    name = CharField(
        'Название цеха',
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
        return f'Цех №{self.number} - {self.name}'
