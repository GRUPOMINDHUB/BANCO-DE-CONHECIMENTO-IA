FROM python:3.10-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O Cloud Run exige a porta 8080
EXPOSE 8080

# Se você quer rodar os dois, precisa de um script que inicie ambos 
# OU rodar apenas o Streamlit se ele for a sua interface principal.
# Vou configurar para o Streamlit assumir a porta 8080:

COPY . .
CMD ["python", "servidor.py"]