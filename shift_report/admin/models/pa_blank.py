from django.contrib import admin
from django.utils.html import format_html

from shift_report.models import PABlank, PARecord


class PARecordInline(admin.TabularInline):
    model = PARecord
    extra = 0
    fields = (
        'hour_number',
        'start_time',
        'end_time',
        'planned_quantity',
        'actual_quantity',
        'deviation',
        'downtime_minutes',
        'is_filled',
    )
    readonly_fields = ('deviation',)
    ordering = ('hour_number',)


@admin.register(PABlank)
class PABlankAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'workplace',
        'date',
        'shift',
        'product',
        'blank_type',
        'status_badge',
        'completion_display',
        'total_fact',
        'total_plan',
    )
    list_filter = (
        'status',
        'blank_type',
        'date',
        'shift',
        'workplace__sector__workshop',
        'workplace__sector',
    )
    search_fields = (
        'workplace__name',
        'product__name',
        'product__article',
    )
    date_hierarchy = 'date'
    ordering = ('-date', '-shift__number')
    inlines = [PARecordInline]

    fieldsets = (
        ('Основные данные', {
            'fields': (
                'workplace',
                'date',
                'shift',
                'product',
            )
        }),
        ('Тип и статус', {
            'fields': (
                'blank_type',
                'status',
            )
        }),
        ('Плановые показатели', {
            'fields': (
                'planned_quantity',
                'takt_time',
                'production_rate',
                'hourly_plan',
                'workplace_capacity',
            )
        }),
        ('Итоговые показатели', {
            'fields': (
                'total_plan',
                'total_fact',
                'total_deviation',
                'total_downtime',
                'completion_percentage',
            ),
            'classes': ('collapse',)
        }),
        ('Примечания', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Служебная информация', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = (
        'takt_time',
        'production_rate',
        'hourly_plan',
        'total_plan',
        'total_fact',
        'total_deviation',
        'total_downtime',
        'completion_percentage',
        'created_at',
        'updated_at',
    )

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'active': '#0d6efd',
            'completed': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Выполнение')
    def completion_display(self, obj):
        percentage = obj.completion_percentage
        formatted_percentage = f'{percentage:.1f}'
        if percentage >= 100:
            color = '#198754'  # green
        elif percentage >= 90:
            color = '#ffc107'  # yellow
        else:
            color = '#dc3545'  # red

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            formatted_percentage
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
