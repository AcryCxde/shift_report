from django.contrib import admin
from django.utils.html import format_html

from shift_report.models import DeviationEntry, PARecord


class DeviationEntryInline(admin.TabularInline):
    model = DeviationEntry
    extra = 0
    fields = ('reason', 'duration_minutes', 'responsible', 'comment')
    autocomplete_fields = ['reason', 'responsible']


@admin.register(PARecord)
class PARecordAdmin(admin.ModelAdmin):
    list_display = (
        'blank',
        'hour_number',
        'start_time',
        'end_time',
        'planned_quantity',
        'actual_quantity',
        'deviation_display',
        'downtime_minutes',
        'status_indicator',
    )
    list_filter = (
        'is_filled',
        'blank__date',
        'blank__shift',
        'blank__workplace__sector',
    )
    search_fields = (
        'blank__workplace__name',
        'blank__product__name',
    )
    ordering = ('blank', 'hour_number')
    inlines = [DeviationEntryInline]

    fieldsets = (
        ('Запись', {
            'fields': (
                'blank',
                'hour_number',
                'start_time',
                'end_time',
            )
        }),
        ('План/Факт', {
            'fields': (
                'planned_quantity',
                'cumulative_plan',
                'actual_quantity',
                'cumulative_fact',
            )
        }),
        ('Отклонения', {
            'fields': (
                'deviation',
                'cumulative_deviation',
                'downtime_minutes',
            )
        }),
        ('Статус заполнения', {
            'fields': (
                'is_filled',
                'filled_at',
                'filled_by',
            )
        }),
    )

    readonly_fields = (
        'deviation',
        'cumulative_plan',
        'cumulative_fact',
        'cumulative_deviation',
    )

    @admin.display(description='Отклонение')
    def deviation_display(self, obj):
        if obj.deviation > 0:
            color = '#198754'
            sign = '+'
        elif obj.deviation < 0:
            color = '#dc3545'
            sign = ''
        else:
            color = '#6c757d'
            sign = ''

        return format_html(
            '<span style="color: {};">{}{}</span>',
            color,
            sign,
            obj.deviation
        )

    @admin.display(description='Статус')
    def status_indicator(self, obj):
        if not obj.is_filled:
            return format_html(
                '<span style="color: {};">⬤ Не заполнено</span>',
                '#6c757d',
            )
        elif obj.actual_quantity >= obj.planned_quantity:
            return format_html(
                '<span style="color: {};">⬤ В норме</span>',
                '#198754'
            )
        elif obj.actual_quantity >= obj.planned_quantity * 0.9:
            return format_html(
                '<span style="color: {};">⬤ Небольшое отставание</span>',
                '#ffc107'
            )
        else:
            return format_html(
                '<span style="color: {};">⬤ Критическое отставание</span>',
                '#dc3545'
            )
