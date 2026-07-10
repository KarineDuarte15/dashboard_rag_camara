import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. Configuração Avançada da Página
# ==========================================
st.set_page_config(
    page_title="Radar Parlamentar | IA & Dados",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. Mock de Dados (Camada GOLD)
# ==========================================
def carregar_dados_gold():
    return {
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_videos": 142,
        "total_proposicoes": 89,
        "kpi_contradicao": 42.5,
        "confiabilidade_rag": 94.2
    }

dados_meta = carregar_dados_gold()

# ==========================================
# 3. Barra Lateral (Filtros e Configurações)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8150/8150100.png", width=80)
    st.title("Parâmetros de Busca")
    st.markdown("Configure a pesquisa vetorial e o LLM.")
    
    with st.form("consulta_rag"):
        nome_deputado = st.text_input("Parlamentar", value="João Silva")
        pergunta_tema = st.text_area("Tema / Pergunta Semântica", value="Qual a postura sobre privatizações?")
        
        st.markdown("**Ajustes do Modelo**")
        temperatura = st.slider("Temperatura (LLM)", 0.0, 1.0, 0.2, help="Valores menores geram respostas mais precisas e menos criativas.")
        
        submit = st.form_submit_button("Executar RAG Híbrido", type="primary")
        
    st.divider()
    st.caption(f"Última sync: {dados_meta['ultima_atualizacao']}")

# ==========================================
# 4. Área Principal
# ==========================================
st.title("🏛️ Radar Parlamentar: Discurso vs. Prática")
st.markdown("Avaliação de coerência política através de **Retrieval-Augmented Generation (RAG)** e Busca Vetorial.")

# Indicadores de Topo
col1, col2, col3, col4 = st.columns(4)
col1.metric("Vídeos Analisados", dados_meta["total_videos"], "+12 esta semana")
col2.metric("Ações na Câmara", dados_meta["total_proposicoes"], "+3 esta semana")
col3.metric("Confiança do RAG", f"{dados_meta['confiabilidade_rag']}%", "Alta", delta_color="normal")
col4.metric("Score de Contradição", f"{dados_meta['kpi_contradicao']}%", "-2.1%", delta_color="inverse")

st.divider()

# ==========================================
# 5. Resultados em Abas (Tabs)
# ==========================================
if submit:
    st.info(f"Análise Semântica concluída para: **{nome_deputado}** | Tema: **{pergunta_tema}**")
    
    tab1, tab2, tab3 = st.tabs(["📊 Análise de Coerência", "📈 Frequência de Temas", "🧠 Auditoria do LLM (Logs)"])
    
    with tab1:
        st.subheader("Termômetro de Contradição")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = dados_meta["kpi_contradicao"],
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#1f77b4"},
                'steps' : [
                    {'range': [0, 30], 'color': "#d6e9c6"},
                    {'range': [30, 70], 'color': "#ffeb99"},
                    {'range': [70, 100], 'color': "#ff9896"}],
            }
        ))
        fig_gauge.update_layout(height=350)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with tab2:
        st.subheader("Comparativo Vetorial: YouTube vs Câmara")
        df_temas = pd.DataFrame({
            "Tema": ["Privatizações", "Segurança Pública", "Educação", "Saúde"],
            "YouTube (Discurso)": [45, 12, 30, 5],
            "Câmara (Prática)": [3, 20, 15, 2]
        })
        df_melt = df_temas.melt(id_vars="Tema", var_name="Origem", value_name="Frequência")
        fig_bar = px.bar(df_melt, x="Tema", y="Frequência", color="Origem", barmode="group",
                         color_discrete_sequence=["#e62020", "#2c9c69"])
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Logs de Recuperação e Geração (RAG)")
        st.markdown("Abaixo estão os trechos exatos (chunks) utilizados pelo Semantic Router para fundamentar a resposta.")
        
        df_evidencias = pd.DataFrame({
            "Fonte RAG": ["YouTube (ID: aB3x)", "Câmara (PL 123/23)"],
            "Trecho Recuperado": [
                "Sou terminantemente contra a venda de estatais...",
                "Voto favorável à privatização do setor elétrico..."
            ],
            "Similaridade (Cosine)": ["0.89", "0.91"],
            "Veredito (LLM)": ["🔴 Contraditório", "🔴 Contraditório"]
        })
        st.dataframe(df_evidencias, use_container_width=True)
else:
    st.info("👈 Utilize o painel lateral para iniciar a análise semântica.")