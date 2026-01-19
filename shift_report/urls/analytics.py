"""
URL-маршруты для аналитики и отчётов.
"""

from django.urls import path

from shift_report.views.analytics import (ChartDataAPIView, ComparisonView,
                                          DashboardAPIView, DashboardView,
                                          DeviationsAnalysisView, ReportsView)

app_name = 'analytics'

urlpatterns = [
    # Главный дашборд
    path('', DashboardView.as_view(), name='dashboard'),

    # Анализ отклонений
    path('deviations/', DeviationsAnalysisView.as_view(), name='deviations'),

    # Сравнительный анализ
    path('comparison/', ComparisonView.as_view(), name='comparison'),

    # Отчёты
    path('reports/', ReportsView.as_view(), name='reports'),

    # API
    path('api/dashboard/', DashboardAPIView.as_view(), name='api_dashboard'),
    path('api/chart/<str:chart_type>/', ChartDataAPIView.as_view(), name='api_chart'),
]
