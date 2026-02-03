"""
Views de autenticação - migradas do Flask servidor.py
Mantém a mesma lógica de validação e sessão.
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Usuario


def index(request):
    """
    Rota: / (Flask)
    Renderiza página de login
    """
    return render(request, 'login.html')


def ia_page(request):
    """
    Rota: /ia (Flask)
    Página do chat - requer autenticação
    """
    if 'usuario' not in request.session:
        return redirect('index')
    return render(request, 'chat.html')


@csrf_exempt  # Temporário - em produção usar CSRF token no frontend
@require_http_methods(["POST"])
def login_endpoint(request):
    """
    Rota: /login (Flask)
    Valida credenciais e cria sessão
    """
    try:
        dados = json.loads(request.body)
        email = dados.get('email')
        senha = dados.get('senha')
        
        # Validação usando Django ORM (email sem diferenciar maiúsculas)
        if not email or not senha:
            return JsonResponse({
                "status": "erro",
                "mensagem": "E-mail e senha são obrigatórios"
            }, status=401)
        
        try:
            usuario = Usuario.objects.get(email__iexact=email.strip())
            if usuario.verificar_senha(senha):
                # Salva usuário na sessão (igual ao Flask)
                request.session['usuario'] = usuario.email
                return JsonResponse({
                    "status": "sucesso",
                    "role": usuario.role
                }, status=200)
        except Usuario.DoesNotExist:
            pass
        
        return JsonResponse({
            "status": "erro",
            "mensagem": "Credenciais inválidas"
        }, status=401)
        
    except Exception as e:
        return JsonResponse({
            "status": "erro",
            "mensagem": str(e)
        }, status=500)


def logout(request):
    """
    Rota: /logout (Flask)
    Limpa sessão e redireciona para login
    """
    request.session.pop('usuario', None)
    return redirect('index')
