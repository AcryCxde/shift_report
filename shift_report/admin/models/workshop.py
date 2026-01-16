from django.contrib import admin

from shift_report.models import Sector, Workshop


class SectorInline(admin.TabularInline):
    model = Sector
    extra = 0
    fields = ('number', 'name', 'is_active')
    show_change_link = True


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'sectors_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'number')
    ordering = ('number',)
    inlines = [SectorInline]

    @admin.display(description='Участков')
    def sectors_count(self, obj):
        return obj.sectors.count()
