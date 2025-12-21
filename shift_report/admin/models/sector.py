from django.contrib import admin

from shift_report.models import Sector


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'workshop')
