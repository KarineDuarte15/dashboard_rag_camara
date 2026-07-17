import sqlite3
import pandas as pd
from google import genai
import warnings

# Ignora avisos do pandas para manter o terminal limpo
warnings.filterwarnings('ignore')

# 1. Configuração da API do LLM usando a nova biblioteca google-genai
API_KEY = "AIzaSyCQH7i2h9q0ejmtkTIBQaSv1E8_WgYy1LY" 
cliente_genai = genai.Client(api_key=API_KEY)

def executar_assistente_legislativo():
    nome_banco = 'camara_dados.db'
    
    # 2. Conectar ao banco para pegar a lista de deputados e temas para validação
    try:
        conn = sqlite3.connect(nome_banco)
        # Lista de deputados para validação
        df_lista_deputados = pd.read_sql_query("SELECT DISTINCT `nome_deputado` FROM votos_deputados", conn)
        lista_nomes_deputados = df_lista_deputados['nome_deputado'].str.upper().tolist()
        
        # Lista de temas únicos existentes no banco
        df_lista_temas = pd.read_sql_query("SELECT DISTINCT tema FROM temas_proposicoes", conn)
        temas_disponiveis = df_lista_temas['tema'].dropna().tolist()
        
    except Exception as e:
        print(f"Erro ao acessar banco de dados inicial: {e}")
        return

    # 3. Interação com o Usuário
    print("="*50)
    print("ASSISTENTE DE ANÁLISE LEGISLATIVA")
    print("="*50)
    
    nome_deputado_input = input("1. Digite o nome do deputado (ex: SILVIA CUNHA): ").strip().upper()
    pergunta_usuario = input("2. Qual a sua pergunta sobre as votações? \n > ").strip()

    print("\nProcessando a sua pergunta via IA...")

# 4. Prompt para o LLM analisar os temas
    prompt_ia = f"""
    Abaixo está uma pergunta feita por um usuário sobre projetos de lei:
    "{pergunta_usuario}"
    
    Abaixo está a lista de temas oficiais registrados no banco de dados da Câmara:
    {temas_disponiveis}
    
    Identifique qual ou quais temas dessa lista melhor correspondem à pergunta.
    Responda APENAS com os nomes exatos dos temas separados por vírgula. Não adicione texto extra.
    """
    
    try:
        resposta_ia = cliente_genai.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt_ia
        )
        # CORREÇÃO 1: Strip mais agressivo para remover pontos e aspas que a IA possa gerar
        temas_identificados = [t.strip(" .\n'\"") for t in resposta_ia.text.split(',')]
        print(f"[IA identificou os temas]: {temas_identificados}")
    except Exception as e:
        print(f"Erro na comunicação com a API Gemini: {e}")
        conn.close()
        return

    print("\nCruzando dados no banco de dados. Aguarde...")

    # 5. Processamento dos Dados
    query_temas = f"SELECT id_proposicao, tema FROM temas_proposicoes"
    df_temas = pd.read_sql_query(query_temas, conn)
    df_temas_filtrado = df_temas[df_temas['tema'].isin(temas_identificados)]
    df_temas_agrupado = df_temas_filtrado.groupby('id_proposicao')['tema'].apply(lambda x: '; '.join(x)).reset_index()

    if df_temas_agrupado.empty:
        print("Nenhuma proposição encontrada com os temas selecionados pela IA.")
        conn.close()
        return

    lista_ids_props = df_temas_agrupado['id_proposicao'].tolist()

    placeholders = ','.join('?' for _ in lista_ids_props)
    query_props = f"SELECT id as id_proposicao, ementa FROM proposicoes WHERE id IN ({placeholders})"
    df_proposicoes = pd.read_sql_query(query_props, conn, params=lista_ids_props)

    query_votacoes = "SELECT id as id_votacao, aprovacao FROM votacoes_detalhes"
    df_votacoes = pd.read_sql_query(query_votacoes, conn)
    
    df_votacoes['id_proposicao'] = df_votacoes['id_votacao'].astype(str).str.split('-').str[0]
    df_votacoes.dropna(subset=['id_proposicao'], inplace=True)

    query_votos = f"SELECT id_votacao, `deputado_.id`, `nome_deputado`, tipoVoto FROM votos_deputados WHERE UPPER(`nome_deputado`) LIKE '%{nome_deputado_input}%'"
    df_votos = pd.read_sql_query(query_votos, conn)

    if df_votos.empty:
        print(f"Não encontramos votos para o deputado: {nome_deputado_input}")
        conn.close()
        return

    # =========================================================
    # CORREÇÃO 2: PADRONIZAÇÃO ABSOLUTA DOS TIPOS (A SOLUÇÃO DO SEU PROBLEMA)
    # Forçamos tudo a ser String (texto), tiramos casas decimais fantasmas (.0) e removemos espaços invisíveis (.strip)
    # =========================================================
    df_proposicoes['id_proposicao'] = df_proposicoes['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_temas_agrupado['id_proposicao'] = df_temas_agrupado['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_votacoes['id_proposicao'] = df_votacoes['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    df_votacoes['id_votacao'] = df_votacoes['id_votacao'].astype(str).str.strip()
    df_votos['id_votacao'] = df_votos['id_votacao'].astype(str).str.strip()
    # =========================================================

# =========================================================
    # 6. Unindo todas as tabelas (O Grande JOIN à prova de falhas)
    # =========================================================
    
    # Primeiro, juntamos as tabelas que sabemos que estão completas (Temas + Votações + Votos) usando 'inner'
    df_final = pd.merge(df_temas_agrupado, df_votacoes[['id_votacao', 'id_proposicao', 'aprovacao']], on='id_proposicao', how='inner')
    df_final = pd.merge(df_final, df_votos, on='id_votacao', how='inner')

    # AGORA O PULO DO GATO: Juntamos as proposições usando 'left'
    # Isso garante que a linha NÃO será apagada se o ID faltar na tabela de proposições!
    df_final = pd.merge(df_final, df_proposicoes, on='id_proposicao', how='left')

    # Preenchemos o buraco deixado pela ementa que faltou com um texto explicativo
    if 'ementa' in df_final.columns:
        df_final['ementa'] = df_final['ementa'].fillna('Ementa não registrada no banco de dados local')
    else:
        df_final['ementa'] = 'Ementa não registrada no banco de dados local'

    # Adiciona a pergunta do usuário
    df_final['pergunta_usuario'] = pergunta_usuario

    # Reorganiza as colunas conforme seu pedido exato
    colunas_ordenadas = [
        'id_proposicao', 'ementa', 
        'tema', 
        'id_votacao', 'aprovacao', 
        'deputado_.id', 'nome_deputado', 'tipoVoto', 
        'pergunta_usuario'
    ]
    
    # Garante que filtra apenas as colunas que existem após os joins
    colunas_presentes = [col for col in colunas_ordenadas if col in df_final.columns]
    df_final = df_final[colunas_presentes]
    
    # 7. Salvar na Tabela Temporária no SQLite
    if not df_final.empty:
        nome_tabela_temp = 'analise_votos_temporaria'
        df_final.to_sql(nome_tabela_temp, conn, if_exists='replace', index=False)
        print("\n" + "="*50)
        print(f"SUCESSO! Tabela '{nome_tabela_temp}' criada no banco de dados.")
        print(f"Foram encontrados {len(df_final)} registros cruzados.")
        print("="*50)
        
        # Exibe uma prévia no terminal
        print("\nPrévia dos resultados:")
        print(df_final[['id_proposicao', 'nome_deputado', 'tipoVoto', 'aprovacao']].head())
    else:
        print("\nNenhum cruzamento encontrado. O deputado não votou em projetos relacionados aos temas encontrados.")

    conn.close()

if __name__ == "__main__":
    executar_assistente_legislativo()