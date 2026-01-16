from django.contrib import admin

from shift_report.models import Sector, Workplace


class WorkplaceInline(admin.TabularInline):
    model = Workplace
    extra = 0
    fields = ('number', 'name', 'equipment_type', 'passport_capacity', 'is_active')
    show_change_link = True


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'workshop', 'workplaces_count', 'is_active')
    list_filter = ('is_active', 'workshop')
    search_fields = ('name', 'number', 'workshop__name')
    ordering = ('workshop__number', 'number')
    inlines = [WorkplaceInline]

    @admin.display(description='Рабочих мест')
    def workplaces_count(self, obj):
        return obj.workplaces.count()
