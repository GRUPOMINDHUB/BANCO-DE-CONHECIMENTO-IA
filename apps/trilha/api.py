"""
API endpoints para o Monitor Graph View - Mindhub OS.
"""
import json
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Max, Count, Q

from apps.usuarios.models import Usuario, RoleChoices
from .models import (
    Mundo, Step, ProgressoAluno, Submissao, NotaSaude,
    StatusProgresso
)


def verificar_monitor(request):
    """Verifica se o usuário logado é monitor ou admin."""
    email = request.session.get('usuario')
    if not email:
        return None, JsonResponse({'error': 'Não autenticado'}, status=401)
    
    try:
        usuario = Usuario.objects.get(email=email)
        if not usuario.pode_validar:
            return None, JsonResponse({'error': 'Acesso negado'}, status=403)
        return usuario, None
    except Usuario.DoesNotExist:
        return None, JsonResponse({'error': 'Usuário não encontrado'}, status=404)


@require_http_methods(["GET"])
def api_monitor_alunos(request):
    """
    GET /api/monitor/alunos/
    Retorna lista de alunos com nota atual e cor para o Graph View.
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    alunos = Usuario.objects.filter(role=RoleChoices.ALUNO, ativo=True)
    
    # Busca última nota de cada aluno
    alunos_data = []
    for aluno in alunos:
        nota_atual = NotaSaude.get_nota_atual(aluno)
        cor = NotaSaude.get_cor_nota(nota_atual)
        mundo_atual = aluno.get_mundo_atual()
        step_atual = aluno.get_step_atual()
        
        # Verifica última submissão
        ultima_submissao = Submissao.objects.filter(
            progresso__aluno=aluno
        ).order_by('-data_envio').first()
        
        # Conta submissões pendentes
        pendentes = Submissao.objects.filter(
            progresso__aluno=aluno,
            aprovado__isnull=True
        ).count()
        
        alunos_data.append({
            'id': aluno.id,
            'nome': aluno.nome or aluno.email.split('@')[0],
            'email': aluno.email,
            'foto': aluno.foto.url if aluno.foto else None,
            'nota': nota_atual,
            'cor': cor,
            'mundo': {
                'numero': mundo_atual.numero,
                'nome': mundo_atual.nome
            } if mundo_atual else None,
            'step': {
                'id': step_atual.id,
                'titulo': step_atual.titulo
            } if step_atual else None,
            'ultima_atividade': ultima_submissao.data_envio.isoformat() if ultima_submissao else None,
            'submissoes_pendentes': pendentes
        })
    
    return JsonResponse({
        'alunos': alunos_data,
        'total': len(alunos_data),
        'cores_legenda': {
            5: {'cor': '#28a745', 'label': 'Excelente'},
            4: {'cor': '#7cb342', 'label': 'Bom'},
            3: {'cor': '#ffc107', 'label': 'Regular'},
            2: {'cor': '#ff9800', 'label': 'Atenção'},
            1: {'cor': '#dc3545', 'label': 'Crítico'},
        }
    })


@require_http_methods(["GET"])
def api_monitor_aluno_detalhe(request, aluno_id):
    """
    GET /api/monitor/aluno/<id>/
    Retorna detalhes completos do aluno para o Drawer lateral.
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    try:
        aluno = Usuario.objects.get(id=aluno_id, role=RoleChoices.ALUNO)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Aluno não encontrado'}, status=404)
    
    # Dados básicos
    nota_atual = NotaSaude.get_nota_atual(aluno)
    mundo_atual = aluno.get_mundo_atual()
    step_atual = aluno.get_step_atual()
    
    # Histórico de notas (últimas 10)
    historico_notas = NotaSaude.objects.filter(aluno=aluno)[:10]
    
    # Progresso geral
    total_steps = Step.objects.filter(ativo=True).count()
    steps_concluidos = ProgressoAluno.objects.filter(
        aluno=aluno,
        status=StatusProgresso.CONCLUIDO
    ).count()
    
    # Submissões pendentes de validação
    submissoes_pendentes = Submissao.objects.filter(
        progresso__aluno=aluno,
        aprovado__isnull=True
    ).select_related('progresso__step').order_by('-data_envio')
    
    # Últimas atividades
    ultimas_submissoes = Submissao.objects.filter(
        progresso__aluno=aluno
    ).select_related('progresso__step').order_by('-data_envio')[:5]
    
    return JsonResponse({
        'aluno': {
            'id': aluno.id,
            'nome': aluno.nome or aluno.email.split('@')[0],
            'email': aluno.email,
            'foto': aluno.foto.url if aluno.foto else None,
            'telefone': aluno.telefone,
            'data_cadastro': aluno.data_cadastro.isoformat(),
        },
        'saude': {
            'nota_atual': nota_atual,
            'cor': NotaSaude.get_cor_nota(nota_atual),
            'historico': [
                {
                    'nota': n.nota,
                    'data': n.data.isoformat(),
                    'automatica': n.automatica,
                    'observacao': n.observacao
                } for n in historico_notas
            ]
        },
        'progresso': {
            'mundo_atual': {
                'numero': mundo_atual.numero,
                'nome': mundo_atual.nome,
                'icone': mundo_atual.icone
            } if mundo_atual else None,
            'step_atual': {
                'id': step_atual.id,
                'titulo': step_atual.titulo,
                'tipo_validacao': step_atual.tipo_validacao
            } if step_atual else None,
            'total_steps': total_steps,
            'steps_concluidos': steps_concluidos,
            'porcentagem': round((steps_concluidos / total_steps * 100) if total_steps > 0 else 0, 1)
        },
        'submissoes_pendentes': [
            {
                'id': s.id,
                'step': s.progresso.step.titulo,
                'tipo': s.progresso.step.tipo_validacao,
                'data_envio': s.data_envio.isoformat(),
                'tem_arquivo': bool(s.arquivo),
                'tem_texto': bool(s.resposta_texto),
            } for s in submissoes_pendentes
        ],
        'ultimas_atividades': [
            {
                'id': s.id,
                'step': s.progresso.step.titulo,
                'data': s.data_envio.isoformat(),
                'status': 'pendente' if s.aprovado is None else ('aprovado' if s.aprovado else 'reprovado')
            } for s in ultimas_submissoes
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_monitor_atualizar_nota(request, aluno_id):
    """
    POST /api/monitor/aluno/<id>/nota/
    Atualiza a nota de saúde do aluno manualmente.
    Body: {"nota": 1-5, "observacao": "opcional"}
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    try:
        aluno = Usuario.objects.get(id=aluno_id, role=RoleChoices.ALUNO)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Aluno não encontrado'}, status=404)
    
    try:
        data = json.loads(request.body)
        nota = int(data.get('nota'))
        observacao = data.get('observacao', '')
        
        if nota < 1 or nota > 5:
            return JsonResponse({'error': 'Nota deve ser entre 1 e 5'}, status=400)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    
    # Cria nova nota de saúde
    nova_nota = NotaSaude.objects.create(
        aluno=aluno,
        nota=nota,
        automatica=False,
        observacao=f"Definida por {monitor.email}. {observacao}".strip()
    )
    
    return JsonResponse({
        'success': True,
        'nota': {
            'id': nova_nota.id,
            'valor': nova_nota.nota,
            'cor': NotaSaude.get_cor_nota(nova_nota.nota),
            'data': nova_nota.data.isoformat()
        }
    })


@require_http_methods(["GET"])
def api_monitor_submissoes_pendentes(request):
    """
    GET /api/monitor/submissoes-pendentes/
    Lista todas as submissões pendentes de validação.
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    submissoes = Submissao.objects.filter(
        aprovado__isnull=True
    ).select_related(
        'progresso__aluno', 
        'progresso__step__mundo'
    ).order_by('data_envio')
    
    return JsonResponse({
        'submissoes': [
            {
                'id': s.id,
                'aluno': {
                    'id': s.progresso.aluno.id,
                    'nome': s.progresso.aluno.nome or s.progresso.aluno.email.split('@')[0],
                    'email': s.progresso.aluno.email,
                    'foto': s.progresso.aluno.foto.url if s.progresso.aluno.foto else None
                },
                'step': {
                    'id': s.progresso.step.id,
                    'titulo': s.progresso.step.titulo,
                    'mundo': s.progresso.step.mundo.nome,
                    'tipo_validacao': s.progresso.step.tipo_validacao
                },
                'data_envio': s.data_envio.isoformat(),
                'arquivo': s.arquivo.url if s.arquivo else None,
                'resposta_texto': s.resposta_texto,
                'resposta_formulario': s.resposta_formulario
            } for s in submissoes
        ],
        'total': submissoes.count()
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_monitor_validar_submissao(request, submissao_id):
    """
    POST /api/monitor/submissao/<id>/validar/
    Aprova ou reprova uma submissão.
    Body: {"aprovado": true/false, "feedback": "texto opcional"}
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    try:
        submissao = Submissao.objects.select_related(
            'progresso__aluno', 'progresso__step'
        ).get(id=submissao_id)
    except Submissao.DoesNotExist:
        return JsonResponse({'error': 'Submissão não encontrada'}, status=404)
    
    if submissao.aprovado is not None:
        return JsonResponse({'error': 'Submissão já foi validada'}, status=400)
    
    try:
        data = json.loads(request.body)
        aprovado = data.get('aprovado')
        feedback = data.get('feedback', '')
        
        if aprovado is None:
            return JsonResponse({'error': 'Campo aprovado é obrigatório'}, status=400)
        
        if not aprovado and not feedback:
            return JsonResponse({'error': 'Feedback é obrigatório para reprovação'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    
    # Valida a submissão
    if aprovado:
        submissao.aprovar(monitor, feedback)
        mensagem = 'Submissão aprovada com sucesso'
    else:
        submissao.reprovar(monitor, feedback)
        mensagem = 'Submissão reprovada'
    
    return JsonResponse({
        'success': True,
        'message': mensagem,
        'submissao': {
            'id': submissao.id,
            'aprovado': submissao.aprovado,
            'feedback': submissao.feedback,
            'data_validacao': submissao.data_validacao.isoformat()
        },
        'aluno': {
            'id': submissao.progresso.aluno.id,
            'step_status': submissao.progresso.status
        }
    })


@require_http_methods(["GET"])
def api_monitor_estatisticas(request):
    """
    GET /api/monitor/estatisticas/
    Retorna estatísticas gerais para o dashboard.
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    # Total de alunos
    total_alunos = Usuario.objects.filter(role=RoleChoices.ALUNO, ativo=True).count()
    
    # Distribuição por nota
    distribuicao_notas = {}
    for nota in range(1, 6):
        # Conta alunos cuja última nota é igual a 'nota'
        count = 0
        for aluno in Usuario.objects.filter(role=RoleChoices.ALUNO, ativo=True):
            if NotaSaude.get_nota_atual(aluno) == nota:
                count += 1
        distribuicao_notas[nota] = count
    
    # Submissões pendentes
    submissoes_pendentes = Submissao.objects.filter(aprovado__isnull=True).count()
    
    # Alunos inativos (sem submissão nos últimos 7 dias)
    limite_inatividade = timezone.now() - timedelta(days=7)
    alunos_ativos = Submissao.objects.filter(
        data_envio__gte=limite_inatividade
    ).values_list('progresso__aluno_id', flat=True).distinct()
    alunos_inativos = Usuario.objects.filter(
        role=RoleChoices.ALUNO, 
        ativo=True
    ).exclude(id__in=alunos_ativos).count()
    
    # Progresso por mundo
    progresso_mundos = []
    for mundo in Mundo.objects.filter(ativo=True).order_by('numero'):
        total_steps_mundo = mundo.steps.count()
        alunos_no_mundo = ProgressoAluno.objects.filter(
            step__mundo=mundo,
            status__in=[StatusProgresso.EM_ANDAMENTO, StatusProgresso.PENDENTE_VALIDACAO]
        ).values('aluno').distinct().count()
        
        progresso_mundos.append({
            'numero': mundo.numero,
            'nome': mundo.nome,
            'icone': mundo.icone,
            'total_steps': total_steps_mundo,
            'alunos_ativos': alunos_no_mundo
        })
    
    return JsonResponse({
        'total_alunos': total_alunos,
        'distribuicao_notas': distribuicao_notas,
        'submissoes_pendentes': submissoes_pendentes,
        'alunos_inativos': alunos_inativos,
        'progresso_mundos': progresso_mundos,
        'cores_notas': {
            str(k): NotaSaude.get_cor_nota(k) for k in range(1, 6)
        }
    })


def enviar_alerta_whatsapp(aluno_id, mensagem=None):
    """
    Placeholder para envio de alertas via WhatsApp.
    TODO: Implementar integração com API do WhatsApp (Twilio, Z-API, etc).
    """
    try:
        aluno = Usuario.objects.get(id=aluno_id)
        telefone = aluno.telefone
        
        if not telefone:
            return {'success': False, 'error': 'Aluno não tem telefone cadastrado'}
        
        # TODO: Implementar chamada real à API do WhatsApp
        # Exemplo com Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=mensagem or f"Olá {aluno.nome}! Você tem atividades pendentes no Mindhub OS.",
        #     from_='whatsapp:+14155238886',
        #     to=f'whatsapp:{telefone}'
        # )
        
        return {
            'success': True, 
            'message': f'Alerta preparado para {telefone} (função placeholder)',
            'aluno_id': aluno_id
        }
    except Usuario.DoesNotExist:
        return {'success': False, 'error': 'Aluno não encontrado'}


@csrf_exempt
@require_http_methods(["POST"])
def api_monitor_enviar_alerta(request, aluno_id):
    """
    POST /api/monitor/aluno/<id>/alerta/
    Envia alerta via WhatsApp para o aluno.
    Body: {"mensagem": "texto opcional"}
    """
    monitor, error = verificar_monitor(request)
    if error:
        return error
    
    try:
        data = json.loads(request.body) if request.body else {}
        mensagem = data.get('mensagem')
    except json.JSONDecodeError:
        mensagem = None
    
    resultado = enviar_alerta_whatsapp(aluno_id, mensagem)
    
    status_code = 200 if resultado['success'] else 400
    return JsonResponse(resultado, status=status_code)
