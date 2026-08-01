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

Após identificar os temas, ocorre o roteamento semântico (`src/semantic_router/`).

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

São coletados (`src/camara/`):

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
camara_dados.db
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

Cada ementa é convertida em embedding (`src/vetorizacao/`).

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

Utiliza (`src/youtube/`):

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

Todos esses dados alimentam o mecanismo RAG (`src/rag/`).

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

A visualização é construída em Streamlit (`app.py` + `src/dashboard/`).

O dashboard apresenta:

- Campo para pesquisa
- Nome do deputado
- Índice de Contradição
- Gráfico de coerência
- Votações relacionadas
- Trechos dos vídeos
- Fontes utilizadas
- Resposta gerada pela IA
