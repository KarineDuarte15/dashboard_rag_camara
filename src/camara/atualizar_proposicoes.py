import sqlite3
import pandas as pd
import requests
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

def atualizar_proposicoes(ano=None):
    nome_banco = 'camara_dados.db'
    ano_atual = ano or datetime.now().year

    print("="*50)
    print(f"ATUALIZADOR DE PROPOSIÇÕES - {ano_atual}")
    print("="*50)

    try:
        conn = sqlite3.connect(nome_banco)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return

    # 1. Pega TODOS os IDs que já existem no seu banco
    print("Lendo banco de dados atual...")
    try:
        df_existentes = pd.read_sql_query("SELECT id FROM proposicoes", conn)
        # Transformamos em um "set" (conjunto) porque a busca nele é instantânea
        ids_banco = set(df_existentes['id'].astype(str))
    except Exception:
        ids_banco = set()
        print("Tabela 'proposicoes' não encontrada. Ela será criada agora.")
    print(f"Temos {len(ids_banco)} proposições salvas atualmente.")

    # 2. Busca os dados do ano atual na API
    print(f"\nBuscando proposições de {ano_atual} na API da Câmara...")
    
    # A API da Câmara é paginada (traz de 100 em 100)
    url_api = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?ano={ano_atual}&itens=100"
    novas_proposicoes = []
    
    while url_api:
        try:
            resposta = requests.get(url_api)
            resposta.raise_for_status()
            dados_json = resposta.json()
            
            lista_proposicoes = dados_json.get('dados', [])
            
            # 3. Compara a API com o Banco
            for prop in lista_proposicoes:
                id_api = str(prop['id'])
                
                # Se o ID da API não estiver no banco, é novidade!
                if id_api not in ids_banco:
                    novas_proposicoes.append(prop)
            
            # Verifica se existe uma próxima página na API
            links = dados_json.get('links', [])
            url_proxima = next((link['href'] for link in links if link['rel'] == 'next'), None)
            url_api = url_proxima
            
        except Exception as e:
            print(f"Erro ao buscar dados na API: {e}")
            break

    # 4. Salva as novidades no SQLite
    if novas_proposicoes:
        df_novas = pd.DataFrame(novas_proposicoes)
        
        # Garante que as colunas da API coincidam com as do CSV original
        # O CSV costuma ter 'id', 'uri', 'siglaTipo', 'numero', 'ano', 'ementa', etc.
        print(f"\nSucesso! Encontramos {len(df_novas)} novas proposições.")
        print("Salvando no banco de dados...")
        
        df_novas.to_sql('proposicoes', conn, if_exists='append', index=False)
        print("Banco de dados atualizado perfeitamente!")
    else:
        print("\nNenhuma proposição nova na Câmara. Seu banco já está 100% atualizado!")

    conn.close()

if __name__ == "__main__":
    atualizar_proposicoes()