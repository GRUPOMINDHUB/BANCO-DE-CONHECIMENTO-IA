"""
URL Configuration - migrado das rotas Flask
Mantém as mesmas URLs do sistema Flask.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')),
    path('', include('apps.ia_engine.urls')),
]
