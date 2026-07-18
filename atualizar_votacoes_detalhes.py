import sqlite3
import pandas as pd
import requests
from datetime import datetime
import calendar
import time
import warnings

warnings.filterwarnings('ignore')

def atualizar_votacoes_detalhes():
    nome_banco = 'camara_dados.db'
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month

    print("="*50)
    print(f"ATUALIZADOR DE VOTAÇÕES - ANO {ano_atual} (Fatiado por Mês)")
    print("="*50)

    try:
        conn = sqlite3.connect(nome_banco)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return

    # 1. Cria a lista rápida com os IDs de votação que você JÁ TEM
    print("Lendo banco de dados atual...")
    try:
        df_existentes = pd.read_sql_query("SELECT id FROM votacoes_detalhes", conn)
        ids_banco = set(df_existentes['id'].astype(str))
    except Exception as e:
        ids_banco = set()
        
    print(f"Temos {len(ids_banco)} votações já cadastradas localmente.")

    novas_votacoes = []

    # 2. Faz um "loop" pelos meses do ano atual até o mês em que estamos
    for mes in range(1, mes_atual + 1):
        ultimo_dia = calendar.monthrange(ano_atual, mes)[1]
        data_inicio = f"{ano_atual}-{mes:02d}-01"
        
        if mes == mes_atual:
            data_fim = hoje.strftime("%Y-%m-%d")
        else:
            data_fim = f"{ano_atual}-{mes:02d}-{ultimo_dia}"

        print(f"\nBuscando mês {mes:02d}... ({data_inicio} até {data_fim})")
        url_api = f"https://dadosabertos.camara.leg.br/api/v2/votacoes?dataInicio={data_inicio}&dataFim={data_fim}&itens=100"
        
        while url_api:
            sucesso_na_requisicao = False
            for tentativa in range(3):
                try:
                    resposta = requests.get(url_api, timeout=20)
                    if resposta.status_code == 200:
                        dados_json = resposta.json()
                        sucesso_na_requisicao = True
                        break 
                    else:
                        print(f"Erro na API (Status {resposta.status_code}). Tentando novamente...")
                        time.sleep(2)
                except requests.exceptions.RequestException:
                    print(f"Lentidão na Câmara (Tentativa {tentativa + 1}/3)...")
                    time.sleep(2)
            
            if not sucesso_na_requisicao:
                print("Falha definitiva ao buscar esta página após 3 tentativas. Pulando...")
                break 
                
            lista_votacoes = dados_json.get('dados', [])
            
            # 3. COMPARAÇÃO UM POR UM PELO ID DA VOTAÇÃO
            for votacao in lista_votacoes:
                id_votacao = str(votacao['id'])
                
                if id_votacao not in ids_banco:
                    # AGORA ESTÁ EXATAMENTE IGUAL AO SEU BANCO DE DADOS
                    novas_votacoes.append({
                        'id': id_votacao,
                        'uri': votacao.get('uri'),
                        'data': votacao.get('data'),
                        'dataHoraRegistro': votacao.get('dataHoraRegistro'),
                        'siglaOrgao': votacao.get('siglaOrgao'),
                        'uriOrgao': votacao.get('uriOrgao'),
                        'idOrgao': votacao.get('idOrgao'),       # Adicionado!
                        'uriEvento': votacao.get('uriEvento'),
                        'idEvento': votacao.get('idEvento'),     # Adicionado!
                        'descricao': votacao.get('descricao'),
                        'aprovacao': votacao.get('aprovacao')
                    })
            
            links = dados_json.get('links', [])
            url_proxima = next((link['href'] for link in links if link['rel'] == 'next'), None)
            url_api = url_proxima
            
            time.sleep(0.2)

    # 4. Salva as novidades na sua tabela
    if novas_votacoes:
        # Colocamos o DataFrame na mesma ordem exata das suas colunas só por garantia
        colunas_ordem = ['id', 'uri', 'data', 'dataHoraRegistro', 'siglaOrgao', 
                         'uriOrgao', 'idOrgao', 'uriEvento', 'idEvento', 'descricao', 'aprovacao']
        df_novas = pd.DataFrame(novas_votacoes, columns=colunas_ordem)
        
        print(f"\nSucesso! Adicionando {len(df_novas)} novas votações.")
        df_novas.to_sql('votacoes_detalhes', conn, if_exists='append', index=False)
        print("Tabela 'votacoes_detalhes' atualizada perfeitamente!")
    else:
        print("\nNenhuma votação nova encontrada para o período. Seu banco está 100% atualizado!")

    conn.close()

if __name__ == "__main__":
    atualizar_votacoes_detalhes()