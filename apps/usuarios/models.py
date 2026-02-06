"""
Models do app Usuarios.
Mantém compatibilidade com a tabela existente usuarios.db do Flask.
"""
from django.db import models
from django.contrib.auth.hashers import check_password, identify_hasher, make_password


class Usuario(models.Model):
    """
    Modelo de Usuário - compatível com a tabela criada em criar_banco.py
    """
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255)  # Em produção, usar hash
    role = models.CharField(max_length=50, default='user', blank=True)
    nome = models.CharField(max_length=150, blank=True)
    sobrenome = models.CharField(max_length=150, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    email_verificado = models.BooleanField(default=True)
    codigo_verificacao = models.CharField(max_length=10, null=True, blank=True)
    codigo_expira_em = models.DateTimeField(null=True, blank=True)
    codigo_usado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usuarios'  # Usa a mesma tabela do Flask
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return self.email
    
    def verificar_senha(self, senha):
        """
        Verifica se a senha fornecida corresponde à senha armazenada.
        Mantém compatibilidade com validação do Flask (texto plano).
        """
        try:
            identify_hasher(self.senha)
            return check_password(senha, self.senha)
        except Exception:
            return self.senha == senha

    def set_password(self, senha):
        """
        Armazena a senha com hash seguro para novos cadastros.
        """
        self.senha = make_password(senha)
