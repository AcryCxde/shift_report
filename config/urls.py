"""
URL configuration for shift_report project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Приложение shift_report
    path('', include('shift_report.urls')),
]
