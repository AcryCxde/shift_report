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

    # Модули будут добавлены в следующих этапах:
    # path('master/', include('shift_report.urls.master', namespace='master')),
    # path('analytics/', include('shift_report.urls.analytics', namespace='analytics')),
]
