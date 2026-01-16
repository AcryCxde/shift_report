from django.db.models import (BooleanField, CharField, Model,
                              PositiveIntegerField, TextField)


class Product(Model):
    """
    Продукция (номенклатура)

    Содержит информацию о производимой продукции,
    включая нормативные показатели времени.
    """

    class Meta:
        verbose_name = 'Продукция'
        verbose_name_plural = 'Продукция'
        ordering = ['name']

    name = CharField(
        'Наименование',
        max_length=255,
    )

    article = CharField(
        'Артикул',
        max_length=100,
        unique=True,
    )

    unit = CharField(
        'Единица измерения',
        max_length=50,
        default='шт.',
    )

    takt_time = PositiveIntegerField(
        'Время такта (норматив), сек',
        null=True,
        blank=True,
        help_text='Интервал времени для производства одной единицы продукции',
    )

    cycle_time = PositiveIntegerField(
        'Время цикла (факт), сек',
        null=True,
        blank=True,
        help_text='Фактическое время выполнения всех операций',
    )

    description = TextField(
        'Описание',
        blank=True,
        default='',
    )

    is_active = BooleanField(
        'Активна',
        default=True,
        help_text='Неактивная продукция не отображается в списках выбора',
    )

    def __str__(self):
        return f'{self.article} - {self.name}'
