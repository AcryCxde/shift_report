from django.contrib import admin

from .models import *  # noqa: F403, F401

admin.site.index_title = 'Производственный анализ'
admin.site.site_header = 'Производственный анализ'
