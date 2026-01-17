from django.contrib import admin
from django.utils.html import format_html

from shift_report.models import TakenMeasure


@admin.register(TakenMeasure)
class TakenMeasureAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'deviation_entry',
        'measure_type',
        'description_short',
        'is_resolved_display',
        'created_by',
        'created_at',
    )
    list_filter = (
        'measure_type',
        'created_at',
        'resolved_at',
    )
    search_fields = (
        'description',
        'deviation_entry__reason__name',
    )
    ordering = ('-created_at',)
    autocomplete_fields = ['deviation_entry', 'created_by']

    fieldsets = (
        ('Связь с отклонением', {
            'fields': ('deviation_entry',)
        }),
        ('Мера', {
            'fields': (
                'measure_type',
                'description',
                'resolved_at',
            )
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

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Описание')
    def description_short(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description

    @admin.display(description='Устранено')
    def is_resolved_display(self, obj):
        if obj.is_resolved:
            return format_html(
                '<span style="color: #198754;">✓ Да</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">✗ Нет</span>'
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
