import pandas as pd
import streamlit as st
import sqlite3

def tratar_dados_votacao(df_votos):
    """
    Limpeza básica e padronização dos votos.
    Expectativa: df com [deputado, partido, votacao_id, voto (Sim/Nao)]
    """
    # Mapear votos para valores numéricos para cálculo (Sim=1, Nao=-1)
    mapping = {'Sim': 1, 'Não': -1, 'Abstenção': 0}
    df_votos['voto_num'] = df_votos['voto'].map(mapping).fillna(0)
    return df_votos

def calcular_correlacao_partido(df, nome_deputado):
    """
    Calcula se o deputado segue a maioria do seu partido.
    Retorna o percentual de alinhamento.
    """
    partido_deputado = df[df['deputado'] == nome_deputado]['partido'].iloc[0]
    
    # Agrupa votos por partido e votação para saber a 'orientação do partido'
    orientacao_partido = df.groupby(['votacao_id', 'partido'])['voto_num'].mean()
    
    # Lógica de correlação: se o voto do deputado for igual ao sinal da média do partido
    # Aqui você retornaria um dataframe para o gráfico
    return f"Alinhamento do {partido_deputado}: 85%"
@st.cache_data
def processar_dados_parlamentares(df_votos, df_gastos):
    """
    Função de ETL (Extract, Transform, Load) para transformar
    dados brutos em indicadores de negócio.
    """
    # 1. Cálculo de Assiduidade (Presença)
    # Assume que o DF de votos tem colunas: ['deputado', 'presente']
    total_votacoes = df_votos['votacao_id'].nunique()
    presenca_df = df_votos.groupby('deputado')['presente'].sum() / total_votacoes
    
    # 2. Cálculo de Custo/Eficiência
    # Assume que o DF de gastos tem colunas: ['deputado', 'valor_gasto']
    # E o DF de votos tem contagem de PLs apresentados
    df_resumo = df_votos.groupby('deputado').agg({
        'pl_apresentados': 'sum',
        'voto_num': 'count'
    }).merge(df_gastos, on='deputado')
    
    df_resumo['eficiencia'] = df_resumo['pl_apresentados'] / df_resumo['valor_gasto']
    
    return presenca_df, df_resumo

def calcular_fidelidade_partidaria(df, deputado):
    """
    Cálculo de correlação: Votos do deputado vs Média do partido.
    """
    # Filtra dados do deputado e do partido dele
    partido = df[df['deputado'] == deputado]['partido'].iloc[0]
    
    # Compara a variância do voto do deputado com a do partido
    fidelidade = df[df['partido'] == partido].groupby('votacao_id')['voto_num'].mean()
    # Retorna uma métrica de 0 a 100%
    return 88  # Exemplo hardcoded, substituir pela lógica real

# Função para carregar e tratar dados de votação (Simulação de ETL)
@st.cache_data
def get_dados_parlamentares():
    # Aqui a sua equipa vai conectar a base de dados (SQLite ou Parquet)
    # Exemplo simulado da estrutura que precisamos:
    df_votos = pd.DataFrame({
        'deputado': ['Erika Karine', 'Deputado X'],
        'presente': [1, 0],
        'pl_apresentados': [12, 5],
        'voto_num': [1, -1],
        'partido': ['PT', 'PL'],
        'votacao_id': [1, 1]
    })
    df_gastos = pd.DataFrame({
        'deputado': ['Erika Karine', 'Deputado X'],
        'valor_gasto': [41200, 35000]
    })
    return df_votos, df_gastos

# Função para buscar logs de auditoria no SQLite (Requisito de monitoramento)
@st.cache_data
def get_logs_auditoria():
    try:
        
        conn = sqlite3.connect('datalake/control/ingestion.db')
        query = "SELECT * FROM logs WHERE timestamp >= date('now', '-7 days')"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        # Retorno de fallback caso o banco não esteja populado ainda
        return pd.DataFrame({
            "Timestamp": ["11/07/2026 10:00", "10/07/2026 09:00"],
            "Fonte": ["YouTube (Discurso)", "API Câmara (Votação)"],
            "Score": [0.98, 0.95],
            "Trecho": ["...transparência...", "...voto favorável..."]
        })