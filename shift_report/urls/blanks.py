"""
URL-маршруты для управления бланками ПА.
"""

from django.urls import path

from shift_report.views.blanks import (BlankBulkCreateView, BlankCreateView,
                                       BlankDeleteView, BlankDetailView,
                                       BlankListView, CalculatePlanAPIView,
                                       TemplateCreateView, TemplateDeleteView,
                                       TemplateEditView, TemplateListView,
                                       WorkplaceAPIView)

app_name = 'blanks'

urlpatterns = [
    # Список бланков
    path('', BlankListView.as_view(), name='list'),

    # Создание бланка
    path('create/', BlankCreateView.as_view(), name='create'),
    path('bulk-create/', BlankBulkCreateView.as_view(), name='bulk_create'),

    # Детали и редактирование бланка
    path('<int:blank_id>/', BlankDetailView.as_view(), name='detail'),
    path('<int:blank_id>/delete/', BlankDeleteView.as_view(), name='delete'),

    # Шаблоны
    path('templates/', TemplateListView.as_view(), name='templates'),
    path('templates/create/', TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:template_id>/edit/', TemplateEditView.as_view(), name='template_edit'),
    path('templates/<int:template_id>/delete/', TemplateDeleteView.as_view(), name='template_delete'),

    # API
    path('api/workplace/<int:workplace_id>/', WorkplaceAPIView.as_view(), name='api_workplace'),
    path('api/calculate-plan/', CalculatePlanAPIView.as_view(), name='api_calculate_plan'),
]
