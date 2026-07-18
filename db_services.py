# Arquivo: db_services.py
import sqlite3
import json
import pandas as pd

def obter_lista_deputados():
    """Busca a lista de deputados no banco e formata para o menu dropdown."""
    conn = sqlite3.connect("camara_dados.db")
    try:
        query = "SELECT nome || ' (' || siglaPartido || '-' || siglaUf || ')' AS nome_completo, nome FROM deputados ORDER BY nome"
        df_deps = pd.read_sql_query(query, conn)
        mapeamento = dict(zip(df_deps["nome_completo"], df_deps["nome"]))
        lista = list(mapeamento.keys())
    except Exception:
        lista = ["TIRIRICA (PL-SP)"]
        mapeamento = {"TIRIRICA (PL-SP)": "TIRIRICA"}
    finally:
        conn.close()
    
    return lista, mapeamento

def carregar_auditoria_gold(nome_deputado):
    """Carrega os dados consolidados da camada Gold para exibir no Dashboard."""
    conn = sqlite3.connect("camara_dados.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        row = cursor.execute("SELECT * FROM relatorio_coerencia_gold WHERE UPPER(deputado) LIKE ?", (f"%{nome_deputado.upper()}%",)).fetchone()
        votos_count = cursor.execute("SELECT COUNT(*) FROM votos_gold_youtube WHERE UPPER(nome_parlamentar) LIKE ?", (f"%{nome_deputado.upper()}%",)).fetchone()[0]
        videos_count = cursor.execute("SELECT COUNT(*) FROM transcricoes_gold_youtube WHERE UPPER(deputado) LIKE ?", (f"%{nome_deputado.upper()}%",)).fetchone()[0]
        
        confianca = "ALTA"
        if votos_count > 0:
            # Tenta pegar a taxa de confiança, mas se a coluna não existir, não quebra
            try:
                conf_row = cursor.execute("SELECT taxa_confianca FROM votos_gold_youtube WHERE UPPER(nome_parlamentar) LIKE ?", (f"%{nome_deputado.upper()}%",)).fetchone()
                if conf_row and conf_row[0]: confianca = conf_row[0].upper()
            except sqlite3.OperationalError:
                pass
                
    except Exception:
        row, votos_count, videos_count, confianca = None, 0, 0, "NENHUMA"
    finally:
        conn.close()
    
    if row:
        return {
            "score_contradicacao": row["score_contradicacao"],
            "resumo": row["resumo"],
            "evidencias": json.loads(row["evidencias_json"]) if row["evidencias_json"] else [],
            "pergunta": row["pergunta"],
            "total_videos": videos_count,
            "total_votos": votos_count,
            "confianca": confianca
        }
    return None