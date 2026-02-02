"""
URLs do app Usuarios
Rotas de autenticação migradas do Flask.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Rota: @app.route('/')
    path('', views.index, name='index'),
    
    # Rota: @app.route('/ia')
    path('ia', views.ia_page, name='ia_page'),
    
    # Rota: @app.route('/login', methods=['POST'])
    path('login', views.login_endpoint, name='login'),
    
    # Rota: @app.route('/logout')
    path('logout', views.logout, name='logout'),
]
