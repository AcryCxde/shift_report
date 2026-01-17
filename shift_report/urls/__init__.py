"""
URL-маршруты приложения shift_report.
"""

from django.urls import include, path
from django.views.generic import TemplateView

app_name = 'shift_report'

urlpatterns = [
    # Главная страница
    path('', TemplateView.as_view(template_name='shift_report/home.html'), name='home'),

    # Аутентификация
    path('', include('shift_report.urls.auth')),

    # Модули будут добавлены в следующих этапах:
    # path('operator/', include('shift_report.urls.operator', namespace='operator')),
    # path('master/', include('shift_report.urls.master', namespace='master')),
    # path('analytics/', include('shift_report.urls.analytics', namespace='analytics')),
    # path('api/', include('shift_report.urls.api', namespace='api')),
]
