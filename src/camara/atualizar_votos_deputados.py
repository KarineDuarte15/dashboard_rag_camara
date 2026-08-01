import sqlite3
import pandas as pd
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

def atualizar_votos_por_csv(ano=None):
    nome_banco = 'camara_dados.db'
    ano_atual = ano or datetime.now().year
    
    print("="*50)
    print(f"ATUALIZADOR DE VOTOS VIA CSV - ANO {ano_atual}")
    print("="*50)

    try:
        conn = sqlite3.connect(nome_banco)
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return

    # 1. Pega os IDs de votações que JÁ TEMOS no banco
    print("Lendo a tabela de votos atual...")
    try:
        df_existentes = pd.read_sql_query("SELECT DISTINCT id_votacao FROM votos_deputados", conn)
        ids_banco = set(df_existentes['id_votacao'].astype(str))
    except Exception:
        ids_banco = set()
        print("Aviso: Tabela 'votos_deputados' não encontrada. Ela será criada agora.")

    # 2. Pega os IDs de TODAS as votações para sabermos quais foram "Simbólicas"
    try:
        df_todas_votacoes = pd.read_sql_query("SELECT id FROM votacoes_detalhes", conn)
        ids_todas_votacoes = set(df_todas_votacoes['id'].astype(str))
    except Exception:
        print("Erro: A tabela 'votacoes_detalhes' precisa existir e ter dados primeiro.")
        conn.close()
        return

    # 3. Baixa o CSV Oficial de Votos do Ano Atual com a URL CORRETA DA IMAGEM
    url_csv = f"https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{ano_atual}.csv"
    print(f"\nBaixando arquivo CSV oficial de votos de {ano_atual}...")
    print(f"URL: {url_csv}")
    print("(Isso pode levar alguns segundos dependendo da internet...)")
    
    try:
        df_csv = pd.read_csv(url_csv, sep=';')
    except Exception as e:
        print(f"Erro ao baixar o CSV da Câmara: {e}")
        conn.close()
        return

    # 4. Padroniza as colunas do CSV do governo para o formato do seu banco
    df_csv.rename(columns={
        'idVotacao': 'id_votacao',
        'voto': 'tipoVoto',
        'deputado_id': 'deputado_.id',
        'deputado_nome': 'deputado_.nome',
        'deputado_siglaPartido': 'deputado_.siglaPartido',
        'deputado_siglaUf': 'deputado_.siglaUf'
    }, inplace=True)

    # Converte os IDs para string para garantir a comparação perfeita
    df_csv['id_votacao'] = df_csv['id_votacao'].astype(str)

    # Filtra apenas as colunas que importam para a sua tabela
    colunas_necessarias = ['id_votacao', 'tipoVoto', 'deputado_.id', 'deputado_.nome', 
                           'deputado_.siglaPartido', 'deputado_.siglaUf']
    
    for col in colunas_necessarias:
        if col not in df_csv.columns:
            df_csv[col] = 'N/A' 
            
    df_csv_filtrado = df_csv[colunas_necessarias]

    # 5. O Cruzamento de Dados (Separa APENAS as votações novas)
    print("Processando e filtrando as novidades...")
    df_novos_votos = df_csv_filtrado[~df_csv_filtrado['id_votacao'].isin(ids_banco)]
    df_novos_votos = df_novos_votos.drop_duplicates()

    # 6. Lida com as Votações Simbólicas (Sem votos nominais)
    ids_novos_no_csv = set(df_novos_votos['id_votacao'].astype(str))
    ids_nominais_totais = ids_banco.union(ids_novos_no_csv)
    ids_simbolicas_faltantes = ids_todas_votacoes - ids_nominais_totais

    votos_simbolicos = []
    for id_simbolica in ids_simbolicas_faltantes:
        votos_simbolicos.append({
            'id_votacao': str(id_simbolica),
            'tipoVoto': 'Simbólica/Sem registro',
            'deputado_.id': 0,
            'deputado_.nome': 'N/A',
            'deputado_.siglaPartido': 'N/A',
            'deputado_.siglaUf': 'N/A'
        })

    if votos_simbolicos:
        df_simbolicos = pd.DataFrame(votos_simbolicos)
        df_novos_votos = pd.concat([df_novos_votos, df_simbolicos], ignore_index=True)

    # 7. Salva tudo no banco de dados de uma vez só
    if not df_novos_votos.empty:
        print(f"\nSucesso! Foram encontrados {len(df_novos_votos)} novos registros de votos (incluindo simbólicos).")
        print("Salvando no banco de dados...")
        df_novos_votos.to_sql('votos_deputados', conn, if_exists='append', index=False)
        print("Tabela 'votos_deputados' atualizada perfeitamente!")
    else:
        print("\nNenhum voto novo encontrado. Seu banco já está 100% atualizado!")
        
    conn.close()

if __name__ == "__main__":
    atualizar_votos_por_csv()