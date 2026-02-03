"""
Admin para o app Trilha.
"""
from django.contrib import admin
from .models import Mundo, Step, ProgressoAluno, Submissao, NotaSaude


@admin.register(Mundo)
class MundoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nome', 'icone', 'total_steps', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    ordering = ['numero']


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'mundo', 'ordem', 'tipo_validacao', 'pontos', 'ativo']
    list_filter = ['mundo', 'tipo_validacao', 'ativo']
    search_fields = ['titulo', 'descricao', 'instrucoes']
    ordering = ['mundo__numero', 'ordem']


@admin.register(ProgressoAluno)
class ProgressoAlunoAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'step', 'status', 'data_inicio', 'data_conclusao']
    list_filter = ['status', 'step__mundo']
    search_fields = ['aluno__email', 'step__titulo']
    raw_id_fields = ['aluno', 'step']


@admin.register(Submissao)
class SubmissaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_aluno', 'get_step', 'data_envio', 'aprovado', 'validado_por']
    list_filter = ['aprovado', 'progresso__step__mundo']
    search_fields = ['progresso__aluno__email', 'feedback']
    raw_id_fields = ['progresso', 'validado_por']
    readonly_fields = ['data_envio', 'data_validacao']
    
    def get_aluno(self, obj):
        return obj.progresso.aluno.email
    get_aluno.short_description = 'Aluno'
    
    def get_step(self, obj):
        return obj.progresso.step.titulo
    get_step.short_description = 'Step'


@admin.register(NotaSaude)
class NotaSaudeAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'nota', 'data', 'automatica']
    list_filter = ['nota', 'automatica']
    search_fields = ['aluno__email', 'observacao']
    raw_id_fields = ['aluno']
    readonly_fields = ['data']
