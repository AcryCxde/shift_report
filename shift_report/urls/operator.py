"""
URL-маршруты для интерфейса оператора.
"""

from django.urls import path

from shift_report.views.operator import (BlankDetailView,
                                         OperatorDashboardView, QuickInputView,
                                         ReasonSearchView, RecordInputView)

app_name = 'operator'

urlpatterns = [
    # Главная страница оператора
    path('', OperatorDashboardView.as_view(), name='dashboard'),

    # Детальный просмотр бланка
    path('blank/<int:blank_id>/', BlankDetailView.as_view(), name='blank_detail'),

    # Ввод данных для записи
    path('record/<int:record_id>/input/', RecordInputView.as_view(), name='record_input'),

    # Быстрый ввод (AJAX)
    path('record/<int:record_id>/quick/', QuickInputView.as_view(), name='quick_input'),

    # Поиск причин (API)
    path('reasons/search/', ReasonSearchView.as_view(), name='reason_search'),
]
