"""
URL-маршруты для администрирования системы.
"""

from django.urls import path

from shift_report.views.admin_views import (AdminDashboardView,
                                            DirectoryListView, ExportView,
                                            ImportView, TemplateDownloadView)

app_name = 'shift_admin'

urlpatterns = [
    # Главная панель
    path('', AdminDashboardView.as_view(), name='dashboard'),

    # Импорт/Экспорт
    path('import/', ImportView.as_view(), name='import'),
    path('export/', ExportView.as_view(), name='export'),

    # Шаблоны для импорта
    path('template/<str:template_name>/', TemplateDownloadView.as_view(), name='template'),

    # Справочники
    path('directory/<str:directory_type>/', DirectoryListView.as_view(), name='directory'),
]
