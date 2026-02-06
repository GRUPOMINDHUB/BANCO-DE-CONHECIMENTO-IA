"""
URLs do app Usuarios
Rotas de autenticação migradas do Flask.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Rota: @app.route('/')
    path('', views.index, name='index'),

    # Cadastro
    path('cadastro', views.cadastro_page, name='cadastro'),
    path('signup', views.signup_endpoint, name='signup'),
    path('verificar', views.verificacao_page, name='verificacao_page'),
    path('verificar-email', views.verificar_codigo_endpoint, name='verificar_email'),
    
    # Rota: @app.route('/ia')
    path('ia', views.ia_page, name='ia_page'),
    
    # Rota: @app.route('/login', methods=['POST'])
    path('login', views.login_endpoint, name='login'),
    
    # Rota: @app.route('/logout')
    path('logout', views.logout, name='logout'),
]
