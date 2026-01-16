from django.contrib import admin

from shift_report.models import Workplace


@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'name',
        'sector',
        'equipment_type',
        'passport_capacity',
        'is_active',
    )
    list_filter = ('is_active', 'sector__workshop', 'sector')
    search_fields = ('name', 'number', 'equipment_type', 'sector__name')
    ordering = ('sector__workshop__number', 'sector__number', 'number')

    fieldsets = (
        (None, {
            'fields': ('sector', 'number', 'name')
        }),
        ('Оборудование', {
            'fields': ('equipment_type', 'passport_capacity', 'achieved_capacity')
        }),
        ('Дополнительно', {
            'fields': ('description', 'is_active'),
            'classes': ('collapse',)
        }),
    )
