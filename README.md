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

# 🏗 Arquitetura Geral

```text
Usuário
    │
    ▼
Pergunta + Nome do Deputado
    │
    ▼
LLM identifica os temas
    │
    ▼
Semantic Routing
    │
    ├────────► Pipeline Câmara
    │
    └────────► Pipeline YouTube
                    │
                    ▼
        Recuperação de documentos
                    │
                    ▼
      Cruzamento de dados (RAG)
                    │
                    ▼
      Índice de Contradição
                    │
                    ▼
Relatório Final
                    │
                    ▼
Dashboard Streamlit
```

---

# 🔄 Fluxo Completo do Sistema

## 1. Entrada do usuário

O usuário fornece:

- Nome do deputado
- Pergunta

Exemplo:

```text
Deputado:
Maria Silva

Pergunta:
O deputado é favorável ao meio ambiente?
```

---

# 2. Processamento inicial da pergunta

A pergunta é enviada ao LLM juntamente com a lista de temas existentes nas proposições legislativas.

Entradas:

- Pergunta do usuário
- Lista de temas da Câmara

Exemplo:

Pergunta:

```text
"O deputado é favorável ao meio ambiente?"
```

Resposta do LLM:

```text
Tema Principal:
Meio Ambiente

Temas Relacionados:
Sustentabilidade
Licenciamento Ambiental
Desmatamento
Energia Renovável
```

Saída:

```text
Lista de TAGs
```

---

# 3. Semantic Routing

Após identificar os temas, ocorre o roteamento semântico.

Sua função é direcionar automaticamente a pergunta para os conjuntos de dados corretos.

Exemplo:

```text
TAGS

• Meio Ambiente
• Sustentabilidade
• Energia
• Licenciamento
```

Essas TAGs alimentam dois pipelines paralelos.

---

# 🏛 Pipeline 1 — Dados da Câmara dos Deputados

## 4. Coleta de Dados

Fonte:

- API Dados Abertos da Câmara

São coletados:

- Proposições
- Projetos de Lei
- PECs
- Requerimentos
- Eventos de votação
- Votos individuais

---

## 5. Armazenamento Relacional

Banco:

```text
banco_projetopolitico.db
```

### Tabela: proposicoes

Campos:

```text
id_proposicao
sigla_tipo
numero
ano
ementa
```

---

### Tabela: eventos_votacao

Campos:

```text
id_votacao
id_proposicao_mae
resumo
data_hora
```

---

### Tabela: votos_deputados

Campos:

```text
id_votacao
id_deputado
voto
```

---

# 6. Vetorização das Proposições

Cada ementa é convertida em embedding.

Fluxo:

```text
Texto da Lei
        │
        ▼
Embedding
        │
        ▼
Banco Vetorial
```

---

# 7. Busca Vetorial

A pergunta do usuário também é vetorizada.

Depois ocorre a comparação entre:

```text
Embedding da Pergunta

×

Embeddings das Leis
```

Resultado:

```text
Leis semanticamente relevantes
```

---

# 8. Cache Vetorial

Tabela:

```text
cache_leis_vetorial
```

Campos:

```text
id_proposicao

embedding

tema

score
```

---

# ▶ Pipeline 2 — YouTube

## 9. Busca de Vídeos

Utiliza:

- API YouTube

Pesquisa:

```text
Nome do Deputado

+

TAGs
```

Exemplo:

```text
Maria Silva

+

Meio Ambiente
```

---

# 10. Recuperação dos vídeos

São obtidos:

- ID
- Título
- Data
- Descrição
- Tags

---

## 11. Banco de vídeos

Tabela:

```text
youtube_videos
```

Campos:

```text
id_video

titulo

descricao

data_publicacao

id_deputado
```

---

## 12. Download das transcrições

Cada vídeo possui sua legenda recuperada automaticamente.

---

## 13. Chunking

Cada transcrição é dividida em pequenos blocos.

Tabela:

```text
youtube_chunks
```

Campos:

```text
id_chunk

texto

ordem

id_video
```

---

## 14. Vetorização dos Chunks

Cada trecho é transformado em embedding.

Tabela:

```text
cache_youtube_vetorial
```

---

## 15. Busca Vetorial

Fluxo:

```text
Pergunta

↓

Embedding

↓

Comparação

↓

Trechos mais relevantes
```

---

## 16. Recuperação dos melhores trechos

Resultado:

```text
Lista de Chunks
```

---

## 17. Validação pelo LLM

Os trechos recuperados passam novamente pelo modelo.

Pergunta feita ao LLM:

```text
Esse trecho responde realmente à pergunta?
```

Resposta:

```text
SIM

ou

NÃO
```

Somente os trechos aprovados seguem para a etapa seguinte.

---

# 🔗 União dos Pipelines

Ao final dos dois pipelines temos:

- Leis relacionadas
- Histórico de votação
- Trechos dos vídeos

Todos esses dados alimentam o mecanismo RAG.

---

# 🤖 Retrieval-Augmented Generation (RAG)

O mecanismo RAG recebe:

- Pergunta
- Deputado
- Leis relevantes
- Histórico de votos
- Trechos dos vídeos

A IA produz uma resposta fundamentada utilizando exclusivamente os documentos recuperados.

---

# 📊 Cálculo do Índice de Contradição

O sistema compara:

```text
DISCURSO

×

VOTAÇÕES
```

Exemplo 1

Vídeo:

```text
"Sou totalmente contra aumento de impostos."
```

Histórico:

```text
Votou favoravelmente ao aumento de impostos.
```

Resultado:

```text
Contradição Alta
```

---

Exemplo 2

Vídeo:

```text
"Sou favorável ao SUS."
```

Histórico:

```text
Sempre votou favoravelmente ao SUS.
```

Resultado:

```text
Baixa Contradição
```

---

# 📄 Relatório Final

O relatório apresenta:

- Nome do parlamentar
- Pergunta do usuário
- Temas identificados
- Leis relacionadas
- Histórico de votações
- Trechos recuperados
- Justificativas
- Evidências utilizadas
- Índice de Contradição
- Conclusão produzida pelo LLM

---

# 🖥 Dashboard

A visualização é construída em Streamlit.

O dashboard apresenta:

- Campo para pesquisa
- Nome do deputado
- Índice de Contradição
- Gráfico de coerência
- Votações relacionadas
- Trechos dos vídeos
- Fontes utilizadas
- Resposta gerada pela IA

---

# 🚀 Como executar localmente

## Clonar o projeto

```bash
git clone https://github.com/TEU_USUARIO/dashboard_rag_camara.git
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

## Executar o Dashboard

```bash
streamlit run app.py
```

---

# 📁 Estrutura do Projeto

```text
dashboard_rag_camara/

│
├── app.py
├── requirements.txt
├── README.md
│
├── docs/
│   ├── RUNBOOK.md
│   ├── CARTA_DO_PROJETO.md
│   └── arquitetura.md
│
├── config/
│   └── ingestao.yml
│
├── deploy/
│   ├── ingestor.service
│   └── streamlit.service
│
├── src/
│   ├── ingestao/
│   ├── vetorizacao/
│   ├── rag/
│   ├── semantic_router/
│   ├── youtube/
│   ├── camara/
│   └── dashboard/
│
└── data/
    ├── banco_projetopolitico.db
    ├── embeddings/
    └── cache/
```

---

# 🛠 Runbook de Operações

## Iniciar serviços

```bash
sudo systemctl start ingestor.service
sudo systemctl start streamlit.service
```

---

## Consultar logs

```bash
journalctl -u ingestor.service -f
```

```bash
journalctl -u streamlit.service -f
```

---

## Reiniciar após atualização

```bash
git pull

sudo systemctl restart ingestor.service

sudo systemctl restart streamlit.service
```

---

# 📋 Carta do Projeto

## Identidade

**Nome do Projeto**

Radar Parlamentar

**Tema**

Geopolítica, Dados Públicos e Inteligência Artificial

**Equipe**

- Engenharia de Dados
- Engenharia de Analytics
- Inteligência Artificial

---

## Problema

É difícil para o cidadão verificar se um parlamentar age de forma coerente entre seu discurso público e suas votações.

---

## Propósito

Automatizar essa verificação utilizando Engenharia de Dados, RAG e Inteligência Artificial.

---

## Público-Alvo

- Jornalistas
- Pesquisadores
- Cientistas Políticos
- Cidadãos
- Organizações da Sociedade Civil

---

## Hipótese

Ao cruzar automaticamente discursos públicos e histórico legislativo será possível produzir um indicador transparente de coerência política.

---

## Escopo Técnico

### Fontes

- API Câmara
- API YouTube

### Frequência

A cada 12 horas.

### KPI Principal

Índice de Contradição (%)

### Fora de Escopo

- Comentários do YouTube
- Redes Sociais
- Fake News
- Análise de Sentimento de terceiros

---

# 🧰 Tecnologias Utilizadas

- Python
- Streamlit
- SQLite/PostgreSQL
- Sentence Transformers
- FAISS ou ChromaDB
- LangChain
- OpenAI API
- YouTube Data API
- API Dados Abertos da Câmara
- Docker
- Systemd
- GitHub Actions

---

# 📌 Resultado Esperado

Ao final do processamento, o sistema entrega um relatório baseado em evidências públicas, permitindo ao usuário analisar a coerência entre o discurso e a prática legislativa de um parlamentar de forma transparente, automatizada e fundamentada em documentos oficiais.
