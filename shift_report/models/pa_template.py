from django.db.models import (CASCADE, SET_NULL, BooleanField, CharField,
                              DateTimeField, ForeignKey, Index, Model,
                              PositiveIntegerField, TextField)

from .pa_blank import PABlankType


class PATemplate(Model):
    """
    Шаблон бланка ПА

    Позволяет быстро создавать бланки для типовых заданий.
    Содержит предустановленные параметры: РМ, продукция, плановый объём.

    FR-010: Шаблоны бланков ПА
    """

    class Meta:
        verbose_name = 'Шаблон бланка ПА'
        verbose_name_plural = 'Шаблоны бланков ПА'
        ordering = ['workplace', 'name']
        indexes = [
            Index(fields=['workplace', 'is_active']),
            Index(fields=['created_by']),
        ]

    name = CharField(
        'Название шаблона',
        max_length=255,
        help_text='Например: "Стандартный план - Деталь А"',
    )

    workplace = ForeignKey(
        'shift_report.Workplace',
        verbose_name='Рабочее место',
        related_name='pa_templates',
        on_delete=CASCADE,
    )

    product = ForeignKey(
        'shift_report.Product',
        verbose_name='Продукция',
        related_name='pa_templates',
        on_delete=CASCADE,
    )

    shift = ForeignKey(
        'shift_report.Shift',
        verbose_name='Смена',
        related_name='pa_templates',
        on_delete=CASCADE,
        null=True,
        blank=True,
        help_text='Если указана, шаблон применяется только для этой смены',
    )

    blank_type = CharField(
        'Тип бланка',
        max_length=20,
        choices=PABlankType.choices,
        default=PABlankType.TYPE_1,
    )

    planned_quantity = PositiveIntegerField(
        'Плановый объём, шт',
        help_text='Стандартный план производства',
    )

    # Привязка к дням недели (опционально)
    # 0=Понедельник, 6=Воскресенье
    monday = BooleanField('Понедельник', default=True)
    tuesday = BooleanField('Вторник', default=True)
    wednesday = BooleanField('Среда', default=True)
    thursday = BooleanField('Четверг', default=True)
    friday = BooleanField('Пятница', default=True)
    saturday = BooleanField('Суббота', default=False)
    sunday = BooleanField('Воскресенье', default=False)

    description = TextField(
        'Описание',
        blank=True,
        default='',
    )

    is_active = BooleanField(
        'Активен',
        default=True,
    )

    # Служебные поля
    created_by = ForeignKey(
        'shift_report.Employee',
        verbose_name='Создал',
        related_name='created_templates',
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
        return f'{self.name} ({self.workplace})'

    def is_applicable_for_weekday(self, weekday: int) -> bool:
        """
        Проверяет, применим ли шаблон для указанного дня недели.

        Args:
            weekday: День недели (0=Понедельник, 6=Воскресенье)
        """
        weekday_map = {
            0: self.monday,
            1: self.tuesday,
            2: self.wednesday,
            3: self.thursday,
            4: self.friday,
            5: self.saturday,
            6: self.sunday,
        }
        return weekday_map.get(weekday, False)

    def create_blank(self, date, shift=None, created_by=None):
        """
        Создаёт бланк ПА на основе шаблона.

        Args:
            date: Дата бланка
            shift: Смена (если не указана, берётся из шаблона)
            created_by: Сотрудник, создающий бланк

        Returns:
            PABlank: Созданный бланк
        """
        from .pa_blank import PABlank

        blank = PABlank.objects.create(
            workplace=self.workplace,
            date=date,
            shift=shift or self.shift,
            product=self.product,
            blank_type=self.blank_type,
            planned_quantity=self.planned_quantity,
            created_by=created_by,
        )
        return blank
