"""
Cria usuários de teste para acessar o Mindhub OS.

Uso:
    python manage.py criar_acessos_teste

Credenciais criadas:
    Admin:    admin@mindhub.com    / admin123
    Monitor:  monitor@mindhub.com   / monitor123
    Alunos:   aluno1@mindhub.com  / aluno123  (e aluno2, aluno3...)
"""
from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario, RoleChoices


class Command(BaseCommand):
    help = 'Cria usuários de teste (admin, monitor e alunos) para acessar o sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-senhas',
            action='store_true',
            help='Redefine as senhas dos usuários existentes para os valores padrão'
        )

    def handle(self, *args, **options):
        reset_senhas = options.get('reset_senhas', False)

        acessos = [
            {
                'email': 'admin@mindhub.com',
                'senha': 'admin123',
                'nome': 'Administrador',
                'role': RoleChoices.ADMIN,
            },
            {
                'email': 'monitor@mindhub.com',
                'senha': 'monitor123',
                'nome': 'Monitor Teste',
                'role': RoleChoices.MONITOR,
            },
            {
                'email': 'aluno1@mindhub.com',
                'senha': 'aluno123',
                'nome': 'Maria Silva',
                'role': RoleChoices.ALUNO,
            },
            {
                'email': 'aluno2@mindhub.com',
                'senha': 'aluno123',
                'nome': 'João Santos',
                'role': RoleChoices.ALUNO,
            },
            {
                'email': 'aluno3@mindhub.com',
                'senha': 'aluno123',
                'nome': 'Ana Costa',
                'role': RoleChoices.ALUNO,
            },
            {
                'email': 'aluno4@mindhub.com',
                'senha': 'aluno123',
                'nome': 'Pedro Oliveira',
                'role': RoleChoices.ALUNO,
            },
            {
                'email': 'aluno5@mindhub.com',
                'senha': 'aluno123',
                'nome': 'Carla Lima',
                'role': RoleChoices.ALUNO,
            },
        ]

        self.stdout.write('\n=== Criando acessos de teste ===\n')

        for dados in acessos:
            senha = dados.pop('senha')
            usuario, created = Usuario.objects.update_or_create(
                email=dados['email'],
                defaults={
                    **dados,
                    'ativo': True,
                }
            )

            # Sempre define a senha em texto plano para esses usuários de teste
            # (compatível com verificar_senha que aceita texto plano)
            usuario.senha = senha
            usuario.save()

            acao = 'Criado' if created else 'Atualizado'
            self.stdout.write(
                self.style.SUCCESS(f'  {acao}: {usuario.email} ({usuario.role}) - senha: {senha}')
            )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Acessos criados com sucesso!\n'))
        self.stdout.write('Para ver o Graph View do Monitor:')
        self.stdout.write('  1. Acesse http://localhost:8080/')
        self.stdout.write('  2. Faça login com: monitor@mindhub.com / monitor123')
        self.stdout.write('  3. Você será redirecionado para o painel do Monitor')
        self.stdout.write('  4. Clique em "Graph View" no menu para ver o grafo de alunos')
        self.stdout.write('')
        self.stdout.write('Para admin (Django admin + painel):')
        self.stdout.write('  admin@mindhub.com / admin123')
        self.stdout.write('')
        self.stdout.write('Alunos (para aparecerem no grafo):')
        self.stdout.write('  aluno1@mindhub.com até aluno5@mindhub.com / aluno123')
        self.stdout.write('='*50 + '\n')
