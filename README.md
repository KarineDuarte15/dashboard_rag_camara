# ⚖️ Radar Parlamentar: Discurso vs. Prática

## 📖 Visão Geral

O **Radar Parlamentar: Discurso vs. Prática** é um projeto desenvolvido como artefato final da disciplina de **Engenharia de Dados**.

O objetivo é verificar automaticamente se o discurso público de um parlamentar é coerente com seu histórico de votações na Câmara dos Deputados.

Para isso, o sistema utiliza técnicas modernas de Engenharia de Dados, Recuperação de Informação e Inteligência Artificial, integrando:

- API de Dados Abertos da Câmara dos Deputados
- API do YouTube
- Transcrições de vídeos
- Busca Vetorial (Embeddings)
- Retrieval-Augmented Generation (RAG)
- Semantic Routing
- Large Language Models (LLMs)

Ao final do processamento é gerado um **Índice de Contradição**, indicando o grau de alinhamento entre aquilo que o parlamentar diz em vídeos públicos e como efetivamente votou em proposições legislativas.

---

# 🎯 Objetivos

O projeto possui quatro objetivos principais:

- Automatizar a coleta de informações públicas.
- Cruzar discursos com votações parlamentares.
- Produzir evidências para análise política baseada em dados.
- Gerar um relatório transparente utilizando Inteligência Artificial.

---

# 📚 Documentação

- [docs/arquitetura.md](docs/arquitetura.md) — arquitetura geral, fluxo completo do pipeline (passo a passo), RAG e cálculo do Índice de Contradição.
- [docs/RUNBOOK.md](docs/RUNBOOK.md) — como rodar localmente e operar em produção (Docker/Coolify).
- [docs/CARTA_DO_PROJETO.md](docs/CARTA_DO_PROJETO.md) — identidade, problema, propósito, público-alvo e escopo do projeto.

---

# 📁 Estrutura do Projeto

```text
trabalho2/
│
├── app.py                    # Entrada do dashboard Streamlit
├── orquestrador.py            # Orquestra o pipeline mestre (Câmara + YouTube + auditoria de IA)
├── requirements.txt
├── README.md
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── docs/
│   ├── arquitetura.md
│   ├── RUNBOOK.md
│   └── CARTA_DO_PROJETO.md
│
├── src/
│   ├── camara/                # Sincronização e cruzamento de dados da Câmara
│   ├── semantic_router/        # Classificação de temas da pergunta via LLM
│   ├── vetorizacao/            # Geração e cache de embeddings (Gemini)
│   ├── rag/                    # Busca vetorial + auditoria de coerência (RAG)
│   ├── youtube/                # Ingestão de vídeos e transcrições do YouTube
│   └── dashboard/              # Acesso a dados para o Streamlit
│
└── datalake/                  # Camadas bronze/silver/gold da ingestão do YouTube
```

---

# 🧰 Tecnologias Utilizadas

- Python
- Streamlit
- SQLite
- Google Gemini (embeddings + geração)
- YouTube Data API
- API Dados Abertos da Câmara
- Docker

---

# 📌 Resultado Esperado

O sistema realiza o join entre dados não estruturados (YouTube/LLM) e dados estruturados (API Câmara/Transparência), criando um índice composto de eficiência parlamentar, ao final do processamento, o sistema entrega um relatório baseado em evidências públicas, permitindo ao usuário analisar a coerência entre o discurso e a prática legislativa de um parlamentar de forma transparente, automatizada e fundamentada em documentos oficiais.
