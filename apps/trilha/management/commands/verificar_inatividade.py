"""
Management command para verificar inatividade dos alunos.
Deve ser executado diariamente via cron/scheduler.

Uso:
    python manage.py verificar_inatividade
    python manage.py verificar_inatividade --dias 7
    python manage.py verificar_inatividade --dry-run
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Max

from apps.usuarios.models import Usuario, RoleChoices
from apps.trilha.models import NotaSaude, Submissao


class Command(BaseCommand):
    help = 'Verifica alunos inativos e atualiza nota de saúde para 1 (vermelho)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Número de dias para considerar inatividade (padrão: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem fazer alterações'
        )
        parser.add_argument(
            '--nota',
            type=int,
            default=1,
            help='Nota a ser atribuída aos inativos (padrão: 1)'
        )
    
    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        nota = options['nota']
        
        self.stdout.write(
            self.style.NOTICE(f'Verificando alunos inativos há mais de {dias} dias...')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita'))
        
        limite = timezone.now() - timedelta(days=dias)
        
        # Busca todos os alunos ativos
        alunos = Usuario.objects.filter(role=RoleChoices.ALUNO, ativo=True)
        
        # IDs de alunos com atividade recente
        alunos_ativos_ids = Submissao.objects.filter(
            data_envio__gte=limite
        ).values_list('progresso__aluno_id', flat=True).distinct()
        
        # Filtra alunos inativos
        alunos_inativos = alunos.exclude(id__in=alunos_ativos_ids)
        
        # Filtra apenas aqueles cuja nota atual NÃO é igual à nota de inatividade
        # (para não criar registros duplicados)
        alunos_para_atualizar = []
        for aluno in alunos_inativos:
            nota_atual = NotaSaude.get_nota_atual(aluno)
            if nota_atual != nota:
                alunos_para_atualizar.append(aluno)
        
        if not alunos_para_atualizar:
            self.stdout.write(
                self.style.SUCCESS('Nenhum aluno inativo encontrado (ou todos já têm nota adequada)')
            )
            return
        
        self.stdout.write(
            f'Encontrados {len(alunos_para_atualizar)} alunos inativos para atualizar:'
        )
        
        for aluno in alunos_para_atualizar:
            # Busca última atividade
            ultima_submissao = Submissao.objects.filter(
                progresso__aluno=aluno
            ).order_by('-data_envio').first()
            
            if ultima_submissao:
                dias_inativo = (timezone.now() - ultima_submissao.data_envio).days
                ultima_atividade = ultima_submissao.data_envio.strftime('%d/%m/%Y')
            else:
                dias_inativo = 'N/A'
                ultima_atividade = 'Nunca'
            
            self.stdout.write(
                f'  - {aluno.email} (última atividade: {ultima_atividade}, {dias_inativo} dias)'
            )
            
            if not dry_run:
                NotaSaude.objects.create(
                    aluno=aluno,
                    nota=nota,
                    automatica=True,
                    observacao=f'Inatividade detectada ({dias_inativo} dias sem submissões)'
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY-RUN] {len(alunos_para_atualizar)} alunos seriam atualizados')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Atualizados {len(alunos_para_atualizar)} alunos com nota {nota}')
            )
