from django.contrib import admin

from shift_report.models import DeviationEntry, TakenMeasure


class TakenMeasureInline(admin.TabularInline):
    model = TakenMeasure
    extra = 0
    fields = ('measure_type', 'description', 'resolved_at', 'created_by')


@admin.register(DeviationEntry)
class DeviationEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'record',
        'reason',
        'duration_minutes',
        'responsible',
        'created_at',
    )
    list_filter = (
        'reason__group',
        'reason',
        'record__blank__date',
        'created_at',
    )
    search_fields = (
        'reason__name',
        'comment',
        'record__blank__workplace__name',
    )
    ordering = ('-created_at',)
    inlines = [TakenMeasureInline]
    autocomplete_fields = ['record', 'reason', 'responsible', 'created_by']

    fieldsets = (
        ('Связь с записью ПА', {
            'fields': ('record',)
        }),
        ('Причина отклонения', {
            'fields': (
                'reason',
                'duration_minutes',
                'responsible',
            )
        }),
        ('Комментарий', {
            'fields': ('comment',)
        }),
        ('Служебная информация', {
            'fields': (
                'created_by',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
