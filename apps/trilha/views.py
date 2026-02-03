"""
Views do app Trilha - Mindhub OS.
"""
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

from apps.usuarios.models import Usuario


def verificar_acesso_monitor(request):
    """Verifica se o usuário tem acesso de monitor."""
    email = request.session.get('usuario')
    if not email:
        return None
    
    try:
        usuario = Usuario.objects.get(email=email)
        if usuario.pode_validar:
            return usuario
    except Usuario.DoesNotExist:
        pass
    
    return None


def monitor_dashboard(request):
    """
    Dashboard principal do Monitor.
    Mostra estatísticas e acesso rápido às funcionalidades.
    """
    usuario = verificar_acesso_monitor(request)
    if not usuario:
        return redirect('/')
    
    return render(request, 'trilha/monitor_dashboard.html', {
        'usuario': usuario,
        'page_title': 'Dashboard do Monitor'
    })


def monitor_graph(request):
    """
    Graph View - Visualização em grafo dos alunos.
    Usa D3.js para renderizar os nós.
    """
    usuario = verificar_acesso_monitor(request)
    if not usuario:
        return redirect('/')
    
    return render(request, 'trilha/monitor_graph.html', {
        'usuario': usuario,
        'page_title': 'Visão Geral - Graph View'
    })


def monitor_validar(request):
    """
    Página de validação de submissões.
    Lista submissões pendentes para aprovar/reprovar.
    """
    usuario = verificar_acesso_monitor(request)
    if not usuario:
        return redirect('/')
    
    return render(request, 'trilha/monitor_validar.html', {
        'usuario': usuario,
        'page_title': 'Validar Submissões'
    })
