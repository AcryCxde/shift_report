from django.contrib import admin
from django.utils.html import format_html

from shift_report.models import DeviationGroup, DeviationReason


class DeviationReasonInline(admin.TabularInline):
    model = DeviationReason
    extra = 0
    fields = ('code', 'name', 'order', 'is_active')
    ordering = ('order', 'name')


@admin.register(DeviationGroup)
class DeviationGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color_preview', 'reasons_count', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'name')
    inlines = [DeviationReasonInline]

    @admin.display(description='Цвет')
    def color_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; '
            'border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.color
        )

    @admin.display(description='Причин')
    def reasons_count(self, obj):
        return obj.reasons.count()


@admin.register(DeviationReason)
class DeviationReasonAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'group', 'usage_count', 'order', 'is_active')
    list_filter = ('is_active', 'group')
    search_fields = ('name', 'code', 'group__name')
    ordering = ('group__order', 'order', 'name')

    fieldsets = (
        (None, {
            'fields': ('group', 'code', 'name')
        }),
        ('Настройки', {
            'fields': ('order', 'description', 'is_active')
        }),
    )
