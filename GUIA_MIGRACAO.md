# GUIA DE MIGRAÇÃO: FLASK → DJANGO
# PASSO A PASSO PARA COLOCAR EM PRODUÇÃO

## 📋 PRÉ-REQUISITOS

✅ Python 3.11+
✅ Acesso ao Google Cloud Run
✅ credentials.json (Google Drive API)
✅ OPENAI_API_KEY

---

## 🔧 PASSO 1: CONFIGURAÇÃO INICIAL

### 1.1 Copiar Arquivos Necessários

```bash
# Navegue até django_project/
cd django_project/

# Copie o credentials.json da raiz do projeto Flask
cp ../credentials.json ./credentials.json

# Crie o arquivo .env baseado no exemplo
cp .env.example .env
```

### 1.2 Editar .env

```bash
# Abra o .env e configure:
OPENAI_API_KEY=sua_chave_openai_aqui
DEBUG=False
SECRET_KEY=Mindhub@1417!
PORT=8080
```

---

## 🐍 PASSO 2: INSTALAÇÃO LOCAL

### 2.1 Criar Ambiente Virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2.2 Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2.3 Preparar Banco de Dados

```bash
# Aplica migrações do Django (cria tabelas necessárias)
python manage.py migrate

# IMPORTANTE: Se você já tem o usuarios.db do Flask na raiz do projeto,
# ele será usado automaticamente. Caso contrário, crie um superusuário:
python manage.py createsuperuser
```

**Nota:** O Django está configurado para usar o mesmo `usuarios.db` do Flask, mantendo compatibilidade total.

---

## 🧪 PASSO 3: TESTAR LOCALMENTE

### 3.1 Iniciar Servidor de Desenvolvimento

```bash
python manage.py runserver 8080
```

### 3.2 Validar Funcionalidades

Acesse `http://localhost:8080` e teste:

- [ ] Login funciona
- [ ] Página de chat carrega
- [ ] IA responde perguntas
- [ ] Botão "Atualizar Base" funciona
- [ ] Edição de arquivos funciona
- [ ] Logout funciona

---

## 🚀 PASSO 4: DEPLOY CLOUD RUN

### 4.1 Configurar Google Cloud

```bash
# Fazer login
gcloud auth login

# Definir projeto
gcloud config set project SEU_PROJETO_ID

# Habilitar APIs necessárias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 4.2 Build da Imagem Docker

```bash
# Ainda dentro de django_project/
gcloud builds submit --tag gcr.io/SEU_PROJETO_ID/banco-conhecimento-ia
```

### 4.3 Deploy no Cloud Run

```bash
gcloud run deploy banco-conhecimento-ia \
  --image gcr.io/SEU_PROJETO_ID/banco-conhecimento-ia \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sua_chave_aqui,DEBUG=False \
  --memory 2Gi \
  --timeout 900
```

### 4.4 Obter URL

Após o deploy, o Cloud Run retornará uma URL como:
```
https://banco-conhecimento-ia-xxxxxxx-uc.a.run.app
```

Acesse essa URL para validar.

---

## 🔄 PASSO 5: MIGRAÇÃO DOS DADOS

### Se você já tem usuários cadastrados no Flask:

1. **O banco SQLite é compatível:**
   ```bash
   # Copie usuarios.db do projeto Flask para a raiz do django_project
   cp ../usuarios.db ./usuarios.db
   ```

2. **Os usuários funcionarão imediatamente** pois o Model do Django usa a mesma tabela.

### Se quiser migrar para Django Auth (opcional):

```python
# Script de migração (criar como manage.py command)
from apps.usuarios.models import Usuario
from django.contrib.auth.models import User

for u in Usuario.objects.all():
    User.objects.create_user(
        username=u.email,
        email=u.email,
        password=u.senha  # Usar make_password() em produção
    )
```

---

## 🔐 PASSO 6: SEGURANÇA EM PRODUÇÃO

### 6.1 Atualizar settings.py

```python
# Em config/settings.py para produção:

DEBUG = False

ALLOWED_HOSTS = [
    'banco-conhecimento-ia-xxxxxxx-uc.a.run.app',
    'seu-dominio.com'
]

# Ativar proteção CSRF
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

### 6.2 Hash de Senhas (recomendado)

Atualizar `apps/usuarios/models.py`:

```python
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    # ...
    
    def set_senha(self, senha_plana):
        self.senha = make_password(senha_plana)
    
    def verificar_senha(self, senha_plana):
        return check_password(senha_plana, self.senha)
```

---

## 📊 PASSO 7: MONITORAMENTO

### 7.1 Logs do Cloud Run

```bash
# Ver logs em tempo real
gcloud run services logs read banco-conhecimento-ia --limit=50 --follow
```

### 7.2 Django Admin

Acesse `https://sua-url.run.app/admin` para gerenciar usuários.

---

## 🔄 PASSO 8: ATUALIZAÇÕES FUTURAS

### Para atualizar o código em produção:

```bash
# 1. Fazer alterações no código
# 2. Rebuild da imagem
gcloud builds submit --tag gcr.io/SEU_PROJETO_ID/banco-conhecimento-ia

# 3. Redeploy
gcloud run deploy banco-conhecimento-ia \
  --image gcr.io/SEU_PROJETO_ID/banco-conhecimento-ia
```

---

## 🆘 TROUBLESHOOTING COMUM

### Erro: "ModuleNotFoundError: No module named 'apps'"

**Solução:** Verifique se está rodando de dentro de `django_project/`

### Erro: "EngineIA credentials.json not found"

**Solução:** 
```bash
# Copie credentials.json para django_project/
cp ../credentials.json ./credentials.json
```

### Erro: "CSRF verification failed"

**Solução:** Adicionar `@csrf_exempt` nas views ou configurar CSRF token no frontend.

### IA não responde / Timeout

**Solução:** Aumentar timeout no Cloud Run:
```bash
--timeout 900
```

---

## ✅ CHECKLIST FINAL

Antes de desligar o Flask:

- [ ] Todas as rotas testadas
- [ ] Login funciona
- [ ] IA responde corretamente
- [ ] Edições salvas no Drive
- [ ] Logs sem erros
- [ ] Backup do banco usuarios.db
- [ ] Credenciais seguras (não commitadas)
- [ ] URL Cloud Run documentada
- [ ] Equipe treinada nas mudanças

---

## 📞 SUPORTE

Em caso de problemas:
1. Verificar logs: `gcloud run services logs read banco-conhecimento-ia`
2. Validar variáveis de ambiente
3. Testar localmente primeiro

**Migração completa! 🎉**
