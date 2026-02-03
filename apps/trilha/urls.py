"""
URLs do app Trilha - Mindhub OS.
"""
from django.urls import path
from . import views, api

app_name = 'trilha'

urlpatterns = [
    # Views (páginas)
    path('monitor/', views.monitor_dashboard, name='monitor_dashboard'),
    path('monitor/graph/', views.monitor_graph, name='monitor_graph'),
    path('monitor/validar/', views.monitor_validar, name='monitor_validar'),
    
    # API endpoints para Graph View
    path('api/monitor/alunos/', api.api_monitor_alunos, name='api_monitor_alunos'),
    path('api/monitor/aluno/<int:aluno_id>/', api.api_monitor_aluno_detalhe, name='api_monitor_aluno_detalhe'),
    path('api/monitor/aluno/<int:aluno_id>/nota/', api.api_monitor_atualizar_nota, name='api_monitor_atualizar_nota'),
    path('api/monitor/aluno/<int:aluno_id>/alerta/', api.api_monitor_enviar_alerta, name='api_monitor_enviar_alerta'),
    path('api/monitor/submissoes-pendentes/', api.api_monitor_submissoes_pendentes, name='api_monitor_submissoes_pendentes'),
    path('api/monitor/submissao/<int:submissao_id>/validar/', api.api_monitor_validar_submissao, name='api_monitor_validar_submissao'),
    path('api/monitor/estatisticas/', api.api_monitor_estatisticas, name='api_monitor_estatisticas'),
]
