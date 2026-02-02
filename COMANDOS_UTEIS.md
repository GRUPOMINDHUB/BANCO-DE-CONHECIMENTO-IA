# 🛠️ COMANDOS ÚTEIS - DJANGO

## 📋 COMANDOS PRINCIPAIS

### Desenvolvimento Local

```bash
# Rodar servidor de desenvolvimento
python manage.py runserver 8080

# Rodar em qualquer IP (para testar de outros dispositivos)
python manage.py runserver 0.0.0.0:8080
```

### Migrações de Banco

```bash
# Criar migrações após alterar models.py
python manage.py makemigrations

# Aplicar migrações ao banco
python manage.py migrate

# Ver SQL que será executado
python manage.py sqlmigrate usuarios 0001

# Ver status das migrações
python manage.py showmigrations
```

### Django Admin

```bash
# Criar superusuário para acessar /admin
python manage.py createsuperuser

# Coletar arquivos estáticos (necessário antes de deploy)
python manage.py collectstatic

# Limpar arquivos estáticos coletados
python manage.py collectstatic --clear
```

### Shell Python Interativo

```bash
# Abrir shell Django (com models carregados)
python manage.py shell

# Exemplo de uso:
# >>> from apps.usuarios.models import Usuario
# >>> Usuario.objects.all()
# >>> Usuario.objects.create(email='teste@teste.com', senha='123')
```

### Testes

```bash
# Rodar todos os testes
python manage.py test

# Rodar testes de um app específico
python manage.py test apps.usuarios

# Rodar com verbosidade
python manage.py test --verbosity 2
```

---

## 🐳 DOCKER

### Build Local

```bash
# Build da imagem
docker build -t banco-conhecimento-ia .

# Rodar container localmente
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=sua_chave \
  banco-conhecimento-ia
```

---

## ☁️ GOOGLE CLOUD

### Configuração Inicial

```bash
# Login
gcloud auth login

# Listar projetos
gcloud projects list

# Definir projeto
gcloud config set project SEU_PROJETO_ID

# Habilitar APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Build e Deploy

```bash
# Build da imagem no Cloud Build
gcloud builds submit --tag gcr.io/SEU_PROJETO_ID/banco-conhecimento-ia

# Listar imagens
gcloud container images list

# Deploy no Cloud Run
gcloud run deploy banco-conhecimento-ia \
  --image gcr.io/SEU_PROJETO_ID/banco-conhecimento-ia \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sua_chave,DEBUG=False \
  --memory 2Gi \
  --timeout 900 \
  --max-instances 10

# Listar serviços
gcloud run services list

# Ver detalhes do serviço
gcloud run services describe banco-conhecimento-ia --region us-central1

# Obter URL do serviço
gcloud run services describe banco-conhecimento-ia \
  --region us-central1 \
  --format 'value(status.url)'
```

### Logs

```bash
# Ver logs em tempo real
gcloud run services logs read banco-conhecimento-ia --limit=50 --follow

# Ver logs recentes
gcloud run services logs read banco-conhecimento-ia --limit=100

# Filtrar logs por erro
gcloud run services logs read banco-conhecimento-ia \
  --limit=50 \
  --filter="severity>=ERROR"
```

### Atualizar Variáveis de Ambiente

```bash
# Atualizar env vars sem rebuild
gcloud run services update banco-conhecimento-ia \
  --update-env-vars OPENAI_API_KEY=nova_chave \
  --region us-central1
```

### Deletar Serviço

```bash
# Deletar serviço (cuidado!)
gcloud run services delete banco-conhecimento-ia --region us-central1
```

---

## 🗄️ BANCO DE DADOS

### SQLite (Local)

```bash
# Abrir banco SQLite
sqlite3 usuarios.db

# Comandos dentro do SQLite:
# .tables                  # Listar tabelas
# .schema usuarios         # Ver estrutura da tabela
# SELECT * FROM usuarios;  # Ver todos os usuários
# .exit                    # Sair
```

### Django ORM via Shell

```bash
python manage.py shell

# Comandos úteis:
# >>> from apps.usuarios.models import Usuario
# 
# # Listar todos
# >>> Usuario.objects.all()
# 
# # Contar registros
# >>> Usuario.objects.count()
# 
# # Buscar por email
# >>> Usuario.objects.get(email='teste@teste.com')
# 
# # Filtrar
# >>> Usuario.objects.filter(role='admin')
# 
# # Criar novo
# >>> Usuario.objects.create(email='novo@teste.com', senha='123', role='user')
# 
# # Deletar
# >>> u = Usuario.objects.get(email='teste@teste.com')
# >>> u.delete()
```

---

## 🔍 DEBUG

### Ver todas as URLs disponíveis

```bash
python manage.py show_urls

# Se não tiver o comando instalado:
pip install django-extensions
# Adicionar 'django_extensions' ao INSTALLED_APPS
```

### Verificar configuração

```bash
python manage.py check

# Verificar deploy
python manage.py check --deploy
```

### Limpar cache

```bash
python manage.py clearsessions
```

---

## 📦 DEPENDÊNCIAS

### Instalar

```bash
# Instalar todas
pip install -r requirements.txt

# Instalar uma específica
pip install django-cors-headers

# Atualizar uma específica
pip install --upgrade langchain
```

### Atualizar requirements.txt

```bash
# Exportar dependências atuais
pip freeze > requirements.txt

# Ou manualmente editar requirements.txt
```

---

## 🔐 SEGURANÇA

### Gerar nova SECRET_KEY

```python
python manage.py shell

# >>> from django.core.management.utils import get_random_secret_key
# >>> get_random_secret_key()
# 'nova-chave-secreta-aqui'
```

### Hash de senhas

```python
python manage.py shell

# >>> from django.contrib.auth.hashers import make_password, check_password
# >>> senha_hash = make_password('minhasenha123')
# >>> print(senha_hash)
# >>> check_password('minhasenha123', senha_hash)  # True
```

---

## 📊 PERFORMANCE

### Criar índices no banco

```python
# Em models.py, adicionar:
class Usuario(models.Model):
    email = models.EmailField(unique=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
        ]

# Depois rodar:
# python manage.py makemigrations
# python manage.py migrate
```

---

## 🧹 LIMPEZA

### Arquivos temporários

```bash
# Limpar arquivos .pyc
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete

# Limpar migrações (CUIDADO!)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
```

---

## 📝 ATALHOS ÚTEIS

```bash
# Criar app novo
python manage.py startapp nome_do_app

# Ver estrutura do projeto
tree -I 'venv|__pycache__|*.pyc'  # Linux/Mac
# ou
dir /s /b  # Windows

# Exportar dados
python manage.py dumpdata usuarios.Usuario > usuarios_backup.json

# Importar dados
python manage.py loaddata usuarios_backup.json
```

---

## 🎯 WORKFLOW TÍPICO

### Desenvolvimento

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Instalar/atualizar dependências
pip install -r requirements.txt

# 3. Aplicar migrações
python manage.py migrate

# 4. Rodar servidor
python manage.py runserver 8080

# 5. Fazer alterações no código
# ...

# 6. Se alterou models.py:
python manage.py makemigrations
python manage.py migrate

# 7. Testar
python manage.py test
```

### Deploy

```bash
# 1. Testar localmente
python manage.py runserver 8080

# 2. Coletar static files
python manage.py collectstatic --noinput

# 3. Build e deploy
gcloud builds submit --tag gcr.io/SEU_PROJETO/banco-ia
gcloud run deploy banco-ia --image gcr.io/SEU_PROJETO/banco-ia

# 4. Ver logs
gcloud run services logs read banco-ia --follow
```

---

## 💡 DICAS

### Rodar comando Django sem manage.py

```bash
# Criar alias (Linux/Mac)
alias dj='python manage.py'

# Usar:
dj runserver
dj migrate
dj shell
```

### Ver SQL de uma query

```python
python manage.py shell

# >>> from apps.usuarios.models import Usuario
# >>> print(Usuario.objects.filter(role='admin').query)
```

### Debug com pdb

```python
# Adicionar no código:
import pdb; pdb.set_trace()

# Ou usar breakpoint() (Python 3.7+)
breakpoint()
```

---

**Referência rápida criada! 🎉**
