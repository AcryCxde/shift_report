from django.db.models import CharField, IntegerField, Model


class Workshop(Model):
    """
    Цех

    sectors: list[Sector] - участки внутри цеха
    """
    class Meta:
        verbose_name = 'Цех'
        verbose_name_plural = 'Цеха'

    number = IntegerField(
        'Номер цеха',
        primary_key=True,
    )

    name = CharField(
        'Название цеха'
    )

    def __str__(self):
        return f'Цех №{self.number}'
