import sqlite3
import pandas as pd
import warnings

# Ignora avisos do pandas para manter o terminal limpo
warnings.filterwarnings('ignore')

def processar_cruzamento(nome_deputado_input, pergunta_usuario, temas_identificados, nome_banco='camara_dados.db'):
    """
    Recebe os dados do usuário e os temas da IA para cruzar no banco de dados.
    """
    try:
        conn = sqlite3.connect(nome_banco)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return

    print("\nCruzando dados no banco de dados. Aguarde...")

    # 1. Processamento dos Dados
    query_temas = f"SELECT id_proposicao, tema FROM temas_proposicoes"
    df_temas = pd.read_sql_query(query_temas, conn)
    df_temas_filtrado = df_temas[df_temas['tema'].isin(temas_identificados)]
    
    if df_temas_filtrado.empty:
        print("Nenhuma proposição encontrada com os temas selecionados pela IA.")
        conn.close()
        return
        
    df_temas_agrupado = df_temas_filtrado.groupby('id_proposicao')['tema'].apply(lambda x: '; '.join(x)).reset_index()
    lista_ids_props = df_temas_agrupado['id_proposicao'].tolist()

    placeholders = ','.join('?' for _ in lista_ids_props)
    query_props = f"SELECT id as id_proposicao, ementa FROM proposicoes WHERE id IN ({placeholders})"
    df_proposicoes = pd.read_sql_query(query_props, conn, params=lista_ids_props)

    query_votacoes = "SELECT id as id_votacao, aprovacao FROM votacoes_detalhes"
    df_votacoes = pd.read_sql_query(query_votacoes, conn)
    
    df_votacoes['id_proposicao'] = df_votacoes['id_votacao'].astype(str).str.split('-').str[0]
    df_votacoes.dropna(subset=['id_proposicao'], inplace=True)

    query_votos = f"SELECT id_votacao, `deputado_.id`, `deputado_.nome`, tipoVoto FROM votos_deputados WHERE UPPER(`deputado_.nome`) LIKE '%{nome_deputado_input}%'"
    df_votos = pd.read_sql_query(query_votos, conn)

    if df_votos.empty:
        print(f"Não encontramos votos para o deputado: {nome_deputado_input}")
        conn.close()
        return

    # 2. PADRONIZAÇÃO ABSOLUTA DOS TIPOS
    df_proposicoes['id_proposicao'] = df_proposicoes['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_temas_agrupado['id_proposicao'] = df_temas_agrupado['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_votacoes['id_proposicao'] = df_votacoes['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    df_votacoes['id_votacao'] = df_votacoes['id_votacao'].astype(str).str.strip()
    df_votos['id_votacao'] = df_votos['id_votacao'].astype(str).str.strip()

    # 3. Unindo todas as tabelas (O Grande JOIN)
    df_final = pd.merge(df_temas_agrupado, df_votacoes[['id_votacao', 'id_proposicao', 'aprovacao']], on='id_proposicao', how='inner')
    df_final = pd.merge(df_final, df_votos, on='id_votacao', how='inner')
    df_final = pd.merge(df_final, df_proposicoes, on='id_proposicao', how='left')

    # 4. Limpeza e Organização Final
    if 'ementa' in df_final.columns:
        df_final['ementa'] = df_final['ementa'].fillna('Ementa não registrada no banco de dados local')
    else:
        df_final['ementa'] = 'Ementa não registrada no banco de dados local'

    df_final['pergunta_usuario'] = pergunta_usuario

    colunas_ordenadas = [
        'id_proposicao', 'ementa', 
        'tema', 
        'id_votacao', 'aprovacao', 
        'deputado_.id', 'deputado_.nome', 'tipoVoto', 
        'pergunta_usuario'
    ]
    
    colunas_presentes = [col for col in colunas_ordenadas if col in df_final.columns]
    df_final = df_final[colunas_presentes]
    
    # 5. Salvar na Tabela Temporária no SQLite
    if not df_final.empty:
        nome_tabela_temp = 'analise_votos_temporaria'
        df_final.to_sql(nome_tabela_temp, conn, if_exists='replace', index=False)
        print("\n" + "="*50)
        print(f"SUCESSO! Tabela '{nome_tabela_temp}' criada no banco de dados.")
        print(f"Foram encontrados {len(df_final)} registros cruzados.")
        print("="*50)
        
        print("\nPrévia dos resultados:")
        print(df_final[['id_proposicao', 'deputado_.nome', 'tipoVoto', 'aprovacao']].head())
    else:
        print("\nNenhum cruzamento encontrado. O deputado não votou em projetos relacionados aos temas encontrados.")

    conn.close()