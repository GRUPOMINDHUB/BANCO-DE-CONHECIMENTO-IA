"""
URL Configuration - migrado das rotas Flask
Mantém as mesmas URLs do sistema Flask.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')),
    path('ia/', include('apps.ia_engine.urls')),
]

# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
    ]
