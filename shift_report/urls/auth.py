"""
URL-маршруты для аутентификации.
"""

from django.urls import path

from shift_report.views import (ChangePINView, LoginView, LogoutView,
                                ProfileView)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-pin/', ChangePINView.as_view(), name='change_pin'),
]
