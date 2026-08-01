# Arquivo: src/vetorizacao/mini_database.py
import sqlite3
import logging
from contextlib import contextmanager

DB_NAME = 'camara_dados.db'

@contextmanager
def obter_conexao():
    conn = sqlite3.connect(DB_NAME)
    # O UPPER() nativo do SQLite só cobre ASCII e não maiúsculiza acentos
    # (ex.: "á" fica "á" em vez de "Á"), quebrando comparações de nomes de
    # deputados. Substitui por uma versão Python, ciente de Unicode.
    conn.create_function("UPPER", 1, lambda s: s.upper() if s is not None else None)
    try:
        yield conn
    finally:
        conn.close()

def inicializar_mini_banco():
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            
            # 1. Tabela de Cache Vetorial das Leis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_leis_vetorial (
                    id_proposicao TEXT PRIMARY KEY,
                    vetor_json TEXT NOT NULL
                )
            """)
            
            # 2. Tabela de Histórico de Consultas Vetoriais
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_consultas_vetorial (
                    id_pergunta INTEGER PRIMARY KEY AUTOINCREMENT,
                    texto_pergunta TEXT NOT NULL,
                    vetor_json TEXT NOT NULL,
                    tema_classificado TEXT,
                    data_consulta TEXT
                )
            """)

            # Garante que a coluna 'data_consulta' exista mesmo se a tabela já foi criada antes
            try:
                cursor.execute("ALTER TABLE historico_consultas_vetorial ADD COLUMN data_consulta TEXT")
            except sqlite3.OperationalError:
                pass # Coluna já existe

            # 3. Tabela Gold de Votos (Câmara) com coluna de Confiança
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votos_gold_youtube (
                    id_proposicao TEXT,
                    tema TEXT,
                    ementa TEXT,
                    tipoVoto TEXT,
                    score_similaridade REAL,
                    deputado_nome TEXT,
                    taxa_confianca TEXT
                )
            """)

            # Garante que a coluna 'taxa_confianca' exista mesmo se a tabela já foi criada antes
            try:
                cursor.execute("ALTER TABLE votos_gold_youtube ADD COLUMN taxa_confianca TEXT")
            except sqlite3.OperationalError:
                pass # Coluna já existe

            # 4. Tabela Gold de Transcrições (YouTube)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcricoes_gold_youtube (
                    video_id TEXT,
                    quantidade_trechos INTEGER,
                    texto_completo TEXT,
                    deputado TEXT
                )
            """)

            # 5. Tabela Cadastro de Deputados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deputados (
                    id_deputado TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    partido TEXT,
                    uf TEXT
                )
            """)
            
            conn.commit()
        logging.info("🏛️ Estrutura do banco unificado validada com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar tabelas: {e}")