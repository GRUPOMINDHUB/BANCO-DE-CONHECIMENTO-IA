"""
Views de autenticação - migradas do Flask servidor.py
Mantém a mesma lógica de validação e sessão.
"""
import datetime
import json
import secrets

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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


def cadastro_page(request):
    """
    Tela de cadastro
    """
    return render(request, 'signup.html')


def verificacao_page(request):
    """
    Tela para inserir o codigo de verificacao
    """
    email = request.GET.get('email', '')
    return render(request, 'verificar_email.html', {'email': email})


@csrf_exempt  # Temporário - em produção usar CSRF token no frontend
@require_http_methods(["POST"])
def login_endpoint(request):
    """
    Rota: /login (Flask)
    Valida credenciais e cria sessão
    """
    try:
        dados = json.loads(request.body)
        email = (dados.get('email') or '').strip()
        senha = dados.get('senha')
        
        # Validação usando Django ORM
        try:
            usuario = Usuario.objects.get(email__iexact=email)
            if usuario.verificar_senha(senha):
                if not usuario.email_verificado:
                    return JsonResponse({
                        "status": "erro",
                        "mensagem": "E-mail ainda nao verificado"
                    }, status=403)
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


@require_http_methods(["POST"])
def signup_endpoint(request):
    """
    Cria conta e envia codigo de verificacao por e-mail
    """
    try:
        dados = json.loads(request.body)
        nome = (dados.get('nome') or '').strip()
        sobrenome = (dados.get('sobrenome') or '').strip()
        data_nascimento_str = (dados.get('data_nascimento') or '').strip()
        email = (dados.get('email') or '').strip().lower()
        senha = dados.get('senha') or ''
        confirmacao = dados.get('confirmacao_senha') or ''

        if not all([nome, sobrenome, data_nascimento_str, email, senha, confirmacao]):
            return JsonResponse({
                "status": "erro",
                "mensagem": "Preencha todos os campos obrigatorios"
            }, status=400)

        allowed_domain = settings.SIGNUP_ALLOWED_DOMAIN.lower()
        if not email.endswith(f"@{allowed_domain}"):
            return JsonResponse({
                "status": "erro",
                "mensagem": f"Somente e-mails @{allowed_domain} podem criar conta"
            }, status=400)

        if senha != confirmacao:
            return JsonResponse({
                "status": "erro",
                "mensagem": "As senhas nao conferem"
            }, status=400)

        if Usuario.objects.filter(email__iexact=email).exists():
            return JsonResponse({
                "status": "erro",
                "mensagem": "E-mail ja cadastrado"
            }, status=400)

        try:
            validate_password(senha)
        except ValidationError as exc:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Senha fraca",
                "detalhes": exc.messages
            }, status=400)

        try:
            data_nascimento = datetime.date.fromisoformat(data_nascimento_str)
        except ValueError:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Data de nascimento invalida"
            }, status=400)

        codigo = f"{secrets.randbelow(1000000):06d}"
        expira_em = timezone.now() + datetime.timedelta(
            minutes=settings.SIGNUP_VERIFICATION_EXPIRATION_MINUTES
        )

        usuario = Usuario(
            email=email,
            nome=nome,
            sobrenome=sobrenome,
            data_nascimento=data_nascimento,
            email_verificado=False,
            codigo_verificacao=codigo,
            codigo_expira_em=expira_em,
            codigo_usado=False,
        )
        usuario.set_password(senha)
        usuario.save()

        assunto = "Codigo de verificacao - Mindhub"
        mensagem = (
            f"Ola {nome},\n\n"
            "Use o codigo abaixo para ativar sua conta:\n\n"
            f"{codigo}\n\n"
            f"Valido por {settings.SIGNUP_VERIFICATION_EXPIRATION_MINUTES} minutos."
        )

        try:
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception:
            usuario.delete()
            return JsonResponse({
                "status": "erro",
                "mensagem": "Falha ao enviar e-mail de verificacao"
            }, status=500)

        return JsonResponse({
            "status": "sucesso",
            "mensagem": "Codigo enviado para o e-mail informado"
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "erro",
            "mensagem": "Formato de dados invalido"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "erro",
            "mensagem": str(e)
        }, status=500)


@require_http_methods(["POST"])
def verificar_codigo_endpoint(request):
    """
    Confirma o codigo de verificacao e ativa a conta
    """
    try:
        dados = json.loads(request.body)
        email = (dados.get('email') or '').strip().lower()
        codigo = (dados.get('codigo') or '').strip()

        if not email or not codigo:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Informe o e-mail e o codigo"
            }, status=400)

        try:
            usuario = Usuario.objects.get(email__iexact=email)
        except Usuario.DoesNotExist:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Conta nao encontrada"
            }, status=404)

        if usuario.email_verificado:
            return JsonResponse({
                "status": "sucesso",
                "mensagem": "Conta ja verificada"
            }, status=200)

        if usuario.codigo_usado:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Codigo ja utilizado"
            }, status=400)

        if usuario.codigo_expira_em and timezone.now() > usuario.codigo_expira_em:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Codigo expirado. Solicite um novo cadastro"
            }, status=400)

        if usuario.codigo_verificacao != codigo:
            return JsonResponse({
                "status": "erro",
                "mensagem": "Codigo invalido"
            }, status=400)

        usuario.email_verificado = True
        usuario.codigo_usado = True
        usuario.codigo_verificacao = None
        usuario.codigo_expira_em = None
        usuario.save(update_fields=[
            'email_verificado',
            'codigo_usado',
            'codigo_verificacao',
            'codigo_expira_em'
        ])

        return JsonResponse({
            "status": "sucesso",
            "mensagem": "Conta verificada com sucesso"
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "erro",
            "mensagem": "Formato de dados invalido"
        }, status=400)
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
