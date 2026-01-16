from django.db.models import (CASCADE, BooleanField, CharField, ForeignKey,
                              Model, PositiveIntegerField, TextField)


class DeviationGroup(Model):
    """
    Группа причин отклонений

    Верхний уровень классификатора причин простоев.
    Базовые группы по методологии МУ-55-2024:
    - Организационные
    - Технические
    - Нет поставок
    - Регламентные работы
    - Качество
    """

    class Meta:
        verbose_name = 'Группа причин отклонений'
        verbose_name_plural = 'Группы причин отклонений'
        ordering = ['order', 'name']

    name = CharField(
        'Название группы',
        max_length=255,
    )

    code = CharField(
        'Код группы',
        max_length=50,
        unique=True,
        help_text='Краткий код для идентификации (например: ORG, TECH)',
    )

    color = CharField(
        'Цвет (HEX)',
        max_length=7,
        default='#6c757d',
        help_text='Цвет для визуализации в отчётах',
    )

    order = PositiveIntegerField(
        'Порядок сортировки',
        default=0,
    )

    description = TextField(
        'Описание',
        blank=True,
        default='',
    )

    is_active = BooleanField(
        'Активна',
        default=True,
    )

    def __str__(self):
        return self.name


class DeviationReason(Model):
    """
    Причина отклонения (простоя)

    Конкретная причина внутри группы.
    Используется операторами при фиксации отклонений.
    """

    class Meta:
        verbose_name = 'Причина отклонения'
        verbose_name_plural = 'Причины отклонений'
        ordering = ['group__order', 'order', 'name']

    group = ForeignKey(
        DeviationGroup,
        verbose_name='Группа причин',
        related_name='reasons',
        on_delete=CASCADE,
    )

    name = CharField(
        'Название причины',
        max_length=255,
    )

    code = CharField(
        'Код причины',
        max_length=50,
        unique=True,
        help_text='Краткий код для идентификации',
    )

    order = PositiveIntegerField(
        'Порядок сортировки',
        default=0,
    )

    description = TextField(
        'Описание',
        blank=True,
        default='',
        help_text='Подробное описание или примеры',
    )

    is_active = BooleanField(
        'Активна',
        default=True,
    )

    # Статистика использования (обновляется периодически)
    usage_count = PositiveIntegerField(
        'Количество использований',
        default=0,
        editable=False,
        help_text='Автоматически обновляется для расчёта топ-5 частых причин',
    )

    def __str__(self):
        return f'{self.group.name}: {self.name}'
