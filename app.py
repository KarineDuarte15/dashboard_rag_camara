import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. Configuração da Página
# ==========================================
st.set_page_config(
    page_title="Radar Parlamentar | Coerência e Discurso",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Radar Parlamentar: Discurso vs. Prática")
st.markdown("""
**Propósito:** Analisar a coerência entre o que os parlamentares falam em público (YouTube) 
e como atuam na câmara (Votações e Proposições).
""")

# ==========================================
# 2. Simulação de Dados (Camada GOLD)
# Aqui, futuramente, a tua equipa conectará o banco de dados real.
# ==========================================
def carregar_dados_gold():
    return {
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_videos_processados": 142,
        "total_proposicoes_processadas": 89,
        "kpi_contradicao": 35.5, 
    }

dados_meta = carregar_dados_gold()

# ==========================================
# 3. Metadados de Confiabilidade (Exigência do Professor)
# ==========================================
with st.expander("ℹ️ Metadados e Confiabilidade da Ingestão"):
    col1, col2, col3 = st.columns(3)
    col1.metric("Última Atualização", dados_meta["ultima_atualizacao"])
    col2.metric("Vídeos Analisados (YouTube)", dados_meta["total_videos_processados"])
    col3.metric("Proposições Analisadas (Câmara)", dados_meta["total_proposicoes_processadas"])
    st.caption("Aviso: Dados baseados em RAG (buscas vetoriais) sobre transcrições e ementas públicas.")

st.divider()

# ==========================================
# 4. Interface de Pesquisa (Onde entra a magia do RAG)
# ==========================================
st.subheader("🔍 Nova Consulta Híbrida")
with st.form("consulta_rag"):
    col_a, col_b = st.columns([1, 2])
    nome_deputado = col_a.text_input("Nome do Deputado", value="João Silva (Exemplo)")
    pergunta_tema = col_b.text_input("Qual tema deseja investigar?", value="Qual a postura sobre privatizações?")
    submit = st.form_submit_button("Pesquisar Discurso vs Prática", type="primary")

# ==========================================
# 5. Resultados e Visualizações
# ==========================================
if submit:
    st.success(f"Consulta gerada para: **{nome_deputado}** no tema **{pergunta_tema}**")
    
    # --- KPI PRINCIPAL ---
    st.subheader("Índice de Contradição Identificado")
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = dados_meta["kpi_contradicao"],
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Nível de Contradição (%)"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkred"},
            'steps' : [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "salmon"}],
        }
    ))
    # Visualização 1 (O KPI em si desenhado)
    st.plotly_chart(fig_gauge, use_container_width=False)
    
    st.divider()
    
    # --- VISUALIZAÇÃO 2: Gráfico de Barras ---
    st.subheader("🗣️ Discurso (YouTube) vs. 🏛️ Prática (Câmara)")
    st.markdown("Volume de menções nos vídeos comparado à quantidade de votos/leis por tema.")
    
    df_temas = pd.DataFrame({
        "Tema": ["Privatizações", "Segurança", "Educação", "Saúde"],
        "Menções YouTube": [45, 12, 30, 5],
        "Votos/Proposições": [3, 20, 15, 2]
    })
    
    df_melt = df_temas.melt(id_vars="Tema", var_name="Origem", value_name="Quantidade")
    fig_bar = px.bar(df_melt, x="Tema", y="Quantidade", color="Origem", barmode="group",
                     color_discrete_map={"Menções YouTube": "#FF0000", "Votos/Proposições": "#008000"})
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # --- VISUALIZAÇÃO 3: Tabela de Evidências ---
    st.subheader("📑 Tabela de Evidências (Justificativa da IA)")
    
    df_evidencias = pd.DataFrame({
        "Data": ["10/05/2023", "12/08/2023"],
        "Trecho YouTube (Discurso)": [
            "Sou terminantemente contra a venda de estatais.",
            "O Estado deve ser forte na economia."
        ],
        "Ação na Câmara (Prática)": [
            "Votou SIM na PL 123/23 (Privatização do setor elétrico)",
            "Propôs a PL 456/23 (Abertura de mercado base)"
        ],
        "Veredito (LLM)": ["🔴 Contraditório", "🟡 Parcialmente Contraditório"]
    })
    
    st.dataframe(df_evidencias, use_container_width=True)