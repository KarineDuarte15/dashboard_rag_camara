# 🚀 Como executar localmente

## Clonar o projeto

```bash
git clone https://github.com/KarineDuarte15/dashboard_rag_camara.git
cd dashboard_rag_camara
```

---

## Criar ambiente virtual

```bash
python -m venv .venv
```

Windows

```bash
.\.venv\Scripts\activate
```

Linux/Mac

```bash
source .venv/bin/activate
```

---

## Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Configurar variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

- `GEMINI_API_KEY` — chave da API Gemini (Google AI Studio), usada na vetorização e na auditoria de coerência.
- `YOUTUBE_API_KEY` — necessária apenas para rodar a ingestão fora do modo demo.

---

## Executar o Dashboard

```bash
streamlit run app.py
```

---

# 🛠 Runbook de Operações

O deploy em produção roda via **Docker**, publicado pelo Coolify (ver `Dockerfile` e `docker-compose.yml` na raiz do projeto).

## Build e execução local via Docker

```bash
docker compose up --build
```

O dashboard fica disponível em `http://localhost:8501`.

## Consultar logs do container

```bash
docker compose logs -f web
```

## Reiniciar após atualização

```bash
git pull
docker compose up --build -d
```

## Healthcheck

O `docker-compose.yml` já define um healthcheck HTTP contra `/_stcore/health` do próprio Streamlit (intervalo de 30s, 3 tentativas).
