# Arquivo: app.py
import sys
import os
import traceback
import importlib  # <-- NOVO: Para matar o cache de importação
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Módulos Modulares que criamos
import orquestrador
importlib.reload(orquestrador) # <-- NOVO: Força o Streamlit a ler o orquestrador.py atualizado do disco!
from orquestrador import executar_pipeline_mestre
from db_services import obter_lista_deputados, carregar_auditoria_gold

# ==========================================
# 1. Configuração de Layout e Estado
# ==========================================
st.set_page_config(page_title="Radar Parlamentar", page_icon="🏛️", layout="wide")

if 'rodando' not in st.session_state: st.session_state.rodando = False
if 'logs' not in st.session_state: st.session_state.logs = ""
if 'deputado_atual' not in st.session_state: st.session_state.deputado_atual = None

# ==========================================
# 2. Barra Lateral (Controles)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8150/8150100.png", width=80)
    st.title("Radar Parlamentar")
    
    lista_exibicao, mapeamento_deputados = obter_lista_deputados()

    with st.form("form_auditoria"):
        deputado_sel = st.selectbox("Selecione o Parlamentar", options=lista_exibicao, index=0)
        nome_deputado_input = mapeamento_deputados[deputado_sel]
        pergunta_tema = st.text_area("Tema de Auditoria", value="Como o deputado votou sobre alteração da jornada de trabalho?")
        btn_processar = st.form_submit_button("🔎 Rodar Auditoria Completa", type="primary")

    st.divider()
    if st.button("🛑 Interromper / Limpar Status"):
        st.session_state.rodando = False
        st.session_state.logs = ""
        st.rerun()

# ==========================================
# 3. Observabilidade e Motor (Execução)
# ==========================================
if btn_processar:
    st.session_state.rodando = True
    st.session_state.logs = ""
    st.session_state.deputado_atual = nome_deputado_input

if st.session_state.rodando:
    st.subheader("⚙️ Painel de Observabilidade")
    status_texto = st.empty()
    barra_progresso = st.progress(0)
    log_area = st.empty()

    def atualizar_interface(mensagem, percentual):
        status_texto.info(f"**Status:** {mensagem}")
        barra_progresso.progress(percentual)
        timestamp = datetime.now().strftime('%H:%M:%S')
        st.session_state.logs += f"[{timestamp}] {mensagem}\n"
        log_area.text_area("Console de Logs:", value=st.session_state.logs, height=300, disabled=True)

    try:
        # Executa o mestre
        sucesso = executar_pipeline_mestre(st.session_state.deputado_atual, pergunta_tema, callback_progresso=atualizar_interface)
        
        if sucesso:
            st.toast("Pipeline finalizado com sucesso!", icon="✅")
            st.session_state.rodando = False
            st.rerun()  # SÓ dá rerun e vai para o Dashboard se der 100% SUCESSO
        else:
            # SE FALHAR: Congela a tela aqui para o usuário conseguir ler o console!
            status_texto.error("🛑 O pipeline foi abortado por uma falha interna. Verifique a última linha do console abaixo.")
            st.stop() 
            
    except Exception as e:
        # SE DER CRASH DE CÓDIGO: Congela e cospe o rastro do erro
        st.session_state.logs += f"\n🚨 ERRO CRÍTICO CRASH DE CÓDIGO 🚨\n{traceback.format_exc()}\n"
        log_area.text_area("Console de Logs:", value=st.session_state.logs, height=400, disabled=True)
        status_texto.error("🚨 Ocorreu um erro físico de execução. Analise o rastro acima.")
        st.stop()

# ==========================================
# 4. Interface Principal (Dashboard)
# ==========================================
if not st.session_state.rodando:
    st.title("🏛️ Radar Parlamentar: Discurso vs. Prática")
    
    # Se acabou de processar ou mudou a seleção, busca os dados do deputado correto
    alvo_busca = st.session_state.deputado_atual if st.session_state.deputado_atual else nome_deputado_input
    dados = carregar_auditoria_gold(alvo_busca)

    if not dados:
        st.info("👈 Utilize o menu lateral para pesquisar um tema e iniciar a auditoria.")
    else:
        st.success(f"📌 Resultados da Auditoria para a pergunta: *\"{dados['pergunta']}\"*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vídeos Analisados", dados["total_videos"])
        col2.metric("Votações Avaliadas", dados["total_votos"])
        col3.metric("Confiança Vetorial", dados["confianca"])
        col4.metric("Índice de Contradição", f"{dados['score_contradicacao']}%")

        st.divider()
        col_gauge, col_text = st.columns([1, 2])
        
        with col_gauge:
            st.subheader("Termômetro de Contradição")
            fig = go.Figure(go.Indicator(mode="gauge+number", value=dados["score_contradicacao"], gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#1f77b4"}, 'steps': [{'range': [0, 30], 'color': "#d6e9c6"}, {'range': [30, 70], 'color': "#ffeb99"}, {'range': [70, 100], 'color': "#ff9896"}]}))
            fig.update_layout(height=280, margin=dict(t=0, b=0, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
            
        with col_text:
            st.subheader("Parecer Técnico da IA")
            st.write(dados["resumo"])

        if dados["evidencias"]:
            st.subheader("🔍 Evidências Cruzadas Encontradas")
            st.dataframe(pd.DataFrame(dados["evidencias"]), use_container_width=True)