# Arquivo: sincronizar_deputados.py
import sqlite3
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

DB_NAME = 'camara_dados.db'
API_URL = "https://dadosabertos.camara.leg.br/api/v2/deputados"

def sincronizar_deputados():
    logging.info("🔌 Iniciando conexão com a API da Câmara dos Deputados...")
    
    # 1. Garante que a tabela de deputados existe no banco de dados
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deputados (
            id_deputado TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            partido TEXT,
            uf TEXT
        )
    """)
    conn.commit()

    # 2. Configura a requisição para trazer todos os deputados ativos ordenados por nome
    params = {
        "ordenarPor": "nome",
        "ordem": "asc",
        "itens": 1000  # Puxa todos em uma única página (evita múltiplas requisições)
    }
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers)
        response.raise_for_status()
        dados_api = response.json().get("dados", [])

        if not dados_api:
            logging.warning("⚠️ A API retornou uma lista vazia.")
            return

        logging.info(f"📥 {len(dados_api)} deputados localizados. Preparando gravação...")

        # 3. Formata os dados para inserção em lote
        deputados_formatados = [
            (
                str(dep["id"]),
                dep["nome"].strip().upper(),  # Nome em maiúsculo para padronizar buscas
                dep["siglaPartido"],
                dep["siglaUf"]
            )
            for dep in dados_api
        ]

        # 4. Salva ou atualiza os registros de forma atômica
        cursor.executemany("""
            INSERT OR REPLACE INTO deputados (id_deputado, nome, partido, uf)
            VALUES (?, ?, ?, ?)
        """, deputados_formatados)
        conn.commit()
        
        logging.info("🏆 SUCESSO! Todos os deputados ativos foram salvos na base 'camara_dados.db'.")

    except Exception as e:
        logging.error(f"❌ Falha ao sincronizar com a API: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sincronizar_deputados()