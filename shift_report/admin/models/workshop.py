from django.contrib import admin

from shift_report.models import Sector, Workshop


class SectorInline(admin.StackedInline):
    model = Sector
    extra = 0
    fields = ('number',)


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('number', 'name',)
    inlines = [SectorInline]
