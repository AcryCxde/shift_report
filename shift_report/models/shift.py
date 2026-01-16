from django.db.models import (BooleanField, CharField, Model,
                              PositiveIntegerField, TimeField)


class Shift(Model):
    """
    Смена

    Определяет график работы: время начала/окончания,
    перерывы и расчётный фонд рабочего времени.
    """

    class Meta:
        verbose_name = 'Смена'
        verbose_name_plural = 'Смены'
        ordering = ['number']

    number = PositiveIntegerField(
        'Номер смены',
        unique=True,
    )

    name = CharField(
        'Название смены',
        max_length=100,
        help_text='Например: Первая смена, Дневная, Ночная',
    )

    start_time = TimeField(
        'Время начала',
    )

    end_time = TimeField(
        'Время окончания',
    )

    # Перерывы (в минутах)
    lunch_break = PositiveIntegerField(
        'Обед, мин',
        default=30,
    )

    personal_break = PositiveIntegerField(
        'Личные нужды, мин',
        default=10,
    )

    handover_break = PositiveIntegerField(
        'Приём-передача смены, мин',
        default=10,
    )

    other_break = PositiveIntegerField(
        'Прочие перерывы, мин',
        default=0,
    )

    is_active = BooleanField(
        'Активна',
        default=True,
    )

    def __str__(self):
        return f'{self.name} ({self.start_time.strftime("%H:%M")}-{self.end_time.strftime("%H:%M")})'

    @property
    def total_breaks(self) -> int:
        """Сумма всех перерывов в минутах"""
        return (
            self.lunch_break +
            self.personal_break +
            self.handover_break +
            self.other_break
        )

    @property
    def duration_minutes(self) -> int:
        """Общая продолжительность смены в минутах"""
        from datetime import datetime, timedelta

        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)

        # Если смена переходит через полночь
        if end < start:
            end += timedelta(days=1)

        return int((end - start).total_seconds() / 60)

    @property
    def working_time_minutes(self) -> int:
        """Фонд рабочего времени в минутах (С = время смены - перерывы)"""
        return self.duration_minutes - self.total_breaks

    @property
    def working_time_hours(self) -> float:
        """Фонд рабочего времени в часах"""
        return self.working_time_minutes / 60
