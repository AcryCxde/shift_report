from django.contrib import admin

from shift_report.models import PATemplate


@admin.register(PATemplate)
class PATemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'workplace',
        'product',
        'shift',
        'blank_type',
        'planned_quantity',
        'weekdays_display',
        'is_active',
    )
    list_filter = (
        'is_active',
        'blank_type',
        'workplace__sector__workshop',
        'workplace__sector',
    )
    search_fields = (
        'name',
        'workplace__name',
        'product__name',
        'product__article',
    )
    ordering = ('workplace', 'name')
    autocomplete_fields = ['workplace', 'product', 'shift', 'created_by']

    fieldsets = (
        ('Основные данные', {
            'fields': (
                'name',
                'workplace',
                'product',
                'shift',
            )
        }),
        ('Параметры бланка', {
            'fields': (
                'blank_type',
                'planned_quantity',
            )
        }),
        ('Дни недели', {
            'fields': (
                ('monday', 'tuesday', 'wednesday', 'thursday'),
                ('friday', 'saturday', 'sunday'),
            ),
            'description': 'Выберите дни, когда применяется этот шаблон'
        }),
        ('Дополнительно', {
            'fields': (
                'description',
                'is_active',
            ),
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

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Дни недели')
    def weekdays_display(self, obj):
        days = []
        if obj.monday:
            days.append('Пн')
        if obj.tuesday:
            days.append('Вт')
        if obj.wednesday:
            days.append('Ср')
        if obj.thursday:
            days.append('Чт')
        if obj.friday:
            days.append('Пт')
        if obj.saturday:
            days.append('Сб')
        if obj.sunday:
            days.append('Вс')
        return ', '.join(days) or 'Не выбраны'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
