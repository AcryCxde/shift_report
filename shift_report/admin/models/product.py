from django.contrib import admin

from shift_report.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'article',
        'name',
        'unit',
        'takt_time',
        'cycle_time',
        'is_active',
    )
    list_filter = ('is_active', 'unit')
    search_fields = ('name', 'article', 'description')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'article', 'unit')
        }),
        ('Нормативы времени', {
            'fields': ('takt_time', 'cycle_time'),
            'description': 'Время указывается в секундах'
        }),
        ('Дополнительно', {
            'fields': ('description', 'is_active'),
            'classes': ('collapse',)
        }),
    )
