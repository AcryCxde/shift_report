"""
URL-маршруты приложения shift_report.
"""

from django.urls import include, path

from shift_report.views.auth import (ChangePINView, HomeView, LoginView,
                                     LogoutView, ProfileView)

# Основные URL без namespace для auth
urlpatterns = [
    # Главная страница
    path('', HomeView.as_view(), name='home'),

    # Аутентификация
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-pin/', ChangePINView.as_view(), name='change_pin'),

    # Интерфейс оператора
    path('operator/', include('shift_report.urls.operator', namespace='operator')),

    # Панель мониторинга мастера
    path('master/', include('shift_report.urls.master', namespace='master')),

    # Управление бланками
    path('blanks/', include('shift_report.urls.blanks', namespace='blanks')),

    # Аналитика и отчёты
    path('analytics/', include('shift_report.urls.analytics', namespace='analytics')),

    # Администрирование
    path('system/', include('shift_report.urls.admin_urls', namespace='shift_admin')),
]
