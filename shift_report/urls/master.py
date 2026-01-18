"""
URL-маршруты для панели мониторинга мастера.
"""

from django.urls import path

from shift_report.views.master import (AddMeasureView, BlankMonitorView,
                                       BlankStatusAPIView,
                                       MasterMonitoringView, MonitoringAPIView,
                                       WorkplaceDetailView)

app_name = 'master'

urlpatterns = [
    # Главная панель мониторинга
    path('', MasterMonitoringView.as_view(), name='monitoring'),

    # Детальный просмотр рабочего места
    path('workplace/<int:workplace_id>/', WorkplaceDetailView.as_view(), name='workplace_detail'),

    # Мониторинг бланка
    path('blank/<int:blank_id>/', BlankMonitorView.as_view(), name='blank_monitor'),

    # Добавление меры
    path('deviation/<int:deviation_id>/measure/', AddMeasureView.as_view(), name='add_measure'),

    # API для real-time обновлений
    path('api/status/', MonitoringAPIView.as_view(), name='api_status'),
    path('api/blank/<int:blank_id>/', BlankStatusAPIView.as_view(), name='api_blank_status'),
]
