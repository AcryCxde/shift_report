from django.db.models import (CASCADE, CharField, ForeignKey, IntegerField,
                              Model)

from .workshop import Workshop


class Sector(Model):
    """
    Участок

    workshop: Workshop - связь с определённым цехом
    """
    class Meta:
        verbose_name = 'Участок'
        verbose_name_plural = 'Участки'

    number = IntegerField(
        'Номер участка',
        primary_key=True,
    )

    name = CharField(
        'Название участка'
    )

    workshop = ForeignKey(
        Workshop,
        verbose_name='Цех',
        related_name='sectors',
        on_delete=CASCADE,
    )

    def __str__(self):
        return f'Участок №{self.number}'
