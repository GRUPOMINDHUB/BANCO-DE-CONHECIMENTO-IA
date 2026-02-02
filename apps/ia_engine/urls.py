"""
URLs do app IA Engine
Rotas de IA migradas do Flask.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Rota: @app.route('/perguntar', methods=['POST'])
    path('perguntar', views.perguntar, name='perguntar'),
    
    # Rota: @app.route('/status-atualizacao')
    path('status-atualizacao', views.status_atualizacao, name='status_atualizacao'),
    
    # Rota: @app.route('/executar-edicao', methods=['POST'])
    path('executar-edicao', views.executar_edicao, name='executar_edicao'),
    
    # Rota: @app.route('/forçar-atualizacao', methods=['POST'])
    path('forçar-atualizacao', views.forcar_atualizacao, name='forcar_atualizacao'),
]
