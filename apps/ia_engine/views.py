"""
Views de IA - migradas do Flask servidor.py
Mantém exatamente a mesma lógica de negócio.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import traceback

from .manager import ia_manager


@csrf_exempt
@require_http_methods(["POST"])
def perguntar(request):
    """
    Rota: /perguntar (Flask)
    Envia pergunta para a IA e retorna resposta
    """
    if 'usuario' not in request.session:
        return JsonResponse({"erro": "Acesso negado"}, status=403)
    
    try:
        dados = json.loads(request.body)
        pergunta = dados.get('mensagem')
        
        # Usa o engine via manager singleton
        ia_engine = ia_manager.get_engine()
        res = ia_engine.invoke({"question": pergunta})
        
        return JsonResponse({"resposta": res["answer"]})
        
    except Exception as e:
        return JsonResponse({
            "erro": str(e)
        }, status=500)


def status_atualizacao(request):
    """
    Rota: /status-atualizacao (Flask)
    Retorna status de atualização da base
    """
    return JsonResponse({
        "atualizando": ia_manager.esta_atualizando()
    })


@csrf_exempt
@require_http_methods(["POST"])
def executar_edicao(request):
    """
    Rota: /executar-edicao (Flask)
    Executa edição de arquivo no Drive
    """
    if 'usuario' not in request.session:
        return JsonResponse({"erro": "Não autorizado"}, status=403)
    
    try:
        dados = json.loads(request.body)
        file_id = dados.get('file_id')
        nome_arquivo = dados.get('nome_arquivo')
        texto_edicao = dados.get('texto')
        
        # Usa a instância via manager
        ia_instancia = ia_manager.get_instancia()
        sucesso = ia_instancia.editar_e_salvar_no_drive(
            file_id, nome_arquivo, texto_edicao
        )
        
        if sucesso:
            return JsonResponse({
                "status": "sucesso",
                "mensagem": "Arquivo atualizado no Drive!"
            })
        else:
            return JsonResponse({
                "status": "erro",
                "mensagem": "A função de gravação falhou. Verifique os logs do sistema."
            }, status=500)
            
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(erro_detalhado)
        return JsonResponse({
            "status": "erro",
            "mensagem": str(e),
            "detalhe": erro_detalhado
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def forcar_atualizacao(request):
    """
    Rota: /forçar-atualizacao (Flask)
    Força atualização da base do Drive
    """
    try:
        ia_manager.forcar_atualizacao()
        return JsonResponse({"status": "sucesso"})
    except Exception as e:
        return JsonResponse({
            "status": "erro",
            "mensagem": str(e)
        }, status=500)
