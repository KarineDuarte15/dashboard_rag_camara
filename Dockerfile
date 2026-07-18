# Deploy do dashboard (Streamlit) na VPS via Coolify. Adicionado pelo professor.
# App de página única (app.py) com dados na camada Gold. Não altera o código de vocês.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
EXPOSE 8501
