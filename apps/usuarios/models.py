"""
Models do app Usuarios.
Mantém compatibilidade com a tabela existente usuarios.db do Flask.
"""
from django.db import models


class Usuario(models.Model):
    """
    Modelo de Usuário - compatível com a tabela criada em criar_banco.py
    """
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255)  # Em produção, usar hash
    role = models.CharField(max_length=50, default='user', blank=True)
    
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
        return self.senha == senha
