from django.contrib import admin

from shift_report.models import Shift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'name',
        'start_time',
        'end_time',
        'total_breaks_display',
        'working_time_display',
        'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('number',)

    fieldsets = (
        (None, {
            'fields': ('number', 'name')
        }),
        ('Время смены', {
            'fields': ('start_time', 'end_time')
        }),
        ('Перерывы (в минутах)', {
            'fields': (
                'lunch_break',
                'personal_break',
                'handover_break',
                'other_break',
            ),
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )

    @admin.display(description='Перерывы, мин')
    def total_breaks_display(self, obj):
        return obj.total_breaks

    @admin.display(description='Фонд времени')
    def working_time_display(self, obj):
        hours = obj.working_time_minutes // 60
        minutes = obj.working_time_minutes % 60
        return f'{hours}ч {minutes}мин'
