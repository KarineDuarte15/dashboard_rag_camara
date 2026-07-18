import sqlite3
import pandas as pd
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

def atualizar_temas_por_csv(ano=None):
    nome_banco = 'camara_dados.db'
    ano_atual = ano or datetime.now().year
    
    print("="*50)
    print(f"ATUALIZADOR DE TEMAS VIA CSV - ANO {ano_atual}")
    print("="*50)

    try:
        conn = sqlite3.connect(nome_banco)
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return

    # 1. Pega os IDs que já temos (Super rápido na memória)
    print("Lendo a tabela de temas atual do banco...")
    try:
        df_existentes = pd.read_sql_query("SELECT DISTINCT id_proposicao FROM temas_proposicoes", conn)
        ids_banco = set(df_existentes['id_proposicao'].astype(str))
    except Exception:
        ids_banco = set()
        print("Tabela temas_proposicoes não encontrada. Ela será criada agora.")

    # 2. Baixa o CSV "Dados Abertos" inteiro da Câmara de uma só vez
    # Arquivos do governo usam separador ';' em vez de ','
    url_csv = f"https://dadosabertos.camara.leg.br/arquivos/proposicoesTemas/csv/proposicoesTemas-{ano_atual}.csv"
    print(f"\nBaixando arquivo CSV oficial de {ano_atual} (isso leva só alguns segundos)...")
    
    try:
        df_csv = pd.read_csv(url_csv, sep=';')
    except Exception as e:
        print(f"Erro ao baixar o CSV. Verifique sua conexão ou se o arquivo do ano atual já está disponível: {e}")
        conn.close()
        return

    # 3. Padroniza as colunas do CSV da Câmara para o nosso banco
    # O arquivo deles às vezes vem com 'uriProposicao' em vez de ID limpo.
    if 'idProposicao' in df_csv.columns:
        df_csv['id_proposicao'] = df_csv['idProposicao'].astype(str)
    elif 'uriProposicao' in df_csv.columns:
        # Pega a URI (ex: .../proposicoes/12345) e recorta só o número final
        df_csv['id_proposicao'] = df_csv['uriProposicao'].apply(lambda x: str(x).split('/')[-1])
    else:
        print("Erro: O formato do CSV da Câmara mudou e não encontramos a coluna de ID.")
        return

    if 'tema' not in df_csv.columns:
        print("Erro: A coluna 'tema' não existe no CSV.")
        return

    # Deixa só o que importa
    df_csv_filtrado = df_csv[['id_proposicao', 'tema']]

    # 4. O cruzamento Ninja (Filtra de uma vez só o que é novidade)
    # Pega apenas as linhas do CSV cujo ID NÃO está (~) na nossa lista do banco
    df_novos_temas = df_csv_filtrado[~df_csv_filtrado['id_proposicao'].isin(ids_banco)]
    
    # Remove duplicações acidentais que o governo possa ter mandado
    df_novos_temas = df_novos_temas.drop_duplicates()

    print(f"Total de registros de {ano_atual} lá na Câmara: {len(df_csv_filtrado)}")
    print(f"Novos registros que faltam no seu banco: {len(df_novos_temas)}")

    # 5. Salva de uma vezada só
    if not df_novos_temas.empty:
        print("\nSalvando os temas faltantes no banco de dados...")
        df_novos_temas.to_sql('temas_proposicoes', conn, if_exists='append', index=False)
        print("SUCESSO! Tabela atualizada perfeitamente.")
    else:
        print("\nNenhum tema novo encontrado. Seu banco já está 100% atualizado!")
        
    conn.close()

if __name__ == "__main__":
    atualizar_temas_por_csv()