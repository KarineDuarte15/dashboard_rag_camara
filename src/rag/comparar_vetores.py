# Arquivo: src/rag/comparar_vetores.py
import json
import math
import logging
import pandas as pd
from src.vetorizacao.mini_database import obter_conexao

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def calcular_similaridade_cosseno(vetor_a, vetor_b):
    if not vetor_a or not vetor_b or len(vetor_a) != len(vetor_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vetor_a, vetor_b))
    norm_a = math.sqrt(sum(a * a for a in vetor_a))
    norm_b = math.sqrt(sum(b * b for b in vetor_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def executar_ranking_comparacao(id_pergunta_alvo):
    logging.info(f"🔍 [MÓDULO DE IA] Analisando vetores para a pergunta ID: {id_pergunta_alvo}")
    
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT texto_pergunta, vetor_json FROM historico_consultas_vetorial WHERE id_pergunta = ?", (id_pergunta_alvo,))
        pergunta_dados = cursor.fetchone()
        
    if not pergunta_dados:
        logging.error(f"🛑 ID {id_pergunta_alvo} não localizado.")
        return False, "Nenhuma"
        
    texto_pergunta, vetor_pergunta_json = pergunta_dados
    vetor_pergunta = json.loads(vetor_pergunta_json)

    try:
        with obter_conexao() as conn:
            df_staging_raw = pd.read_sql_query("SELECT * FROM analise_votos_temporaria", conn)
            df_cache = pd.read_sql_query("SELECT id_proposicao, vetor_json FROM cache_leis_vetorial", conn)
    except Exception as e:
        logging.error(f"⚠️ Erro ao ler tabelas do banco: {e}")
        return False, "Nenhuma"

    if df_staging_raw.empty:
        logging.warning("⚠️ Tabela temporária vazia.")
        return False, "Nenhuma"

    df_staging_raw['id_proposicao'] = df_staging_raw['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_cache['id_proposicao'] = df_cache['id_proposicao'].astype(str).str.replace('.0', '', regex=False).str.strip()

    df_staging = pd.merge(df_staging_raw, df_cache, on='id_proposicao', how='inner')

    if df_staging.empty:
        logging.warning("⚠️ Nenhuma proposição da tabela temporária possui vetor correspondente no cache.")
        return False, "Nenhuma"

    df_unique_props = df_staging.drop_duplicates(subset=['id_proposicao']).copy()
    
    # 1. Calcula os scores para todas as leis do lote
    scores_list = []
    for index, row in df_unique_props.iterrows():
        vetor_lei = json.loads(row['vetor_json'])
        score = calcular_similaridade_cosseno(vetor_pergunta, vetor_lei)
        scores_list.append((row['id_proposicao'], score, row['ementa']))

    scores_list = sorted(scores_list, key=lambda x: x[1], reverse=True)

    # 2. LOOP DE FILTRO ADAPTATIVO (Margem de Confiança)
    thresholds = [
        (0.70, "Alta"),    # Margem padrão
        (0.60, "Média"),   # Redução de 10%
        (0.50, "Baixa")    # Redução de 20%
    ]
    
    matched_limit = None
    taxa_confianca = "Nenhuma"
    aprovados = []

    for limit, label in thresholds:
        aprovados = [item for item in scores_list if item[1] >= limit]
        if aprovados:
            matched_limit = limit
            taxa_confianca = label
            break

    # 3. Monta o relatório para o console
    diagnostico_leis = []
    for id_prop, score, ementa in scores_list:
        if matched_limit and score >= matched_limit:
            status = f"🎯 GOLD (>= {matched_limit*100:.0f}%)"
        else:
            status = f"⚠️ REJEITADO (< {matched_limit*100:.0f}%)" if matched_limit else "⚠️ REJEITADO (< 50%)"
        
        diagnostico_leis.append({
            "id_proposicao": id_prop,
            "score": score,
            "score_pct": f"{score * 100:.2f}%",
            "ementa": ementa,
            "status": status
        })

    print("\n" + "="*125)
    print("📊 RELATÓRIO COMPLETO DE ANÁLISE SEMÂNTICA (CÂMARA DOS DEPUTADOS)")
    print("="*125)
    print(f"{'Posição':<8} | {'ID Lei':<10} | {'Aderência':<15} | {'Status':<20} | {'Ementa':<60}")
    print("-" * 125)
    for posicao, item in enumerate(diagnostico_leis, 1):
        ementa_resumida = item['ementa'][:60].replace("\n", " ").strip() + "..." if item['ementa'] else "Ementa não registrada..."
        print(f"{posicao:<8} | {item['id_proposicao']:<10} | {item['score_pct']:<15} | {item['status']:<20} | {ementa_resumida:<60}")
    print("="*125 + "\n")

    # 4. Grava os dados se houver aprovação em algum dos níveis de confiança
    if aprovados:
        logging.info(f"✨ Filtro adaptativo ativado! Limite final: {matched_limit*100:.0f}% | Confiança: {taxa_confianca.upper()}")
        scores_dict = {id_prop: round(score, 4) for id_prop, score, _ in aprovados}
        ids_aprovados = list(scores_dict.keys())
        
        df_gold_final = df_staging[df_staging['id_proposicao'].isin(ids_aprovados)].copy()
        df_gold_final['score_similaridade'] = df_gold_final['id_proposicao'].map(scores_dict)
        df_gold_final['taxa_confianca'] = taxa_confianca  # Registra o nível de confiança na Gold!
        
        if 'vetor_json' in df_gold_final.columns:
            df_gold_final = df_gold_final.drop(columns=['vetor_json'])
        if 'tema' in df_gold_final.columns:
            df_gold_final = df_gold_final.drop(columns=['tema'])

        with obter_conexao() as conn:
            df_gold_final.to_sql('votos_gold_youtube', conn, if_exists='replace', index=False)
        
        logging.info(f"🥇 [CAMADA GOLD] {len(df_gold_final)} registros salvos com Confiança {taxa_confianca.upper()}!")
        limpar_tabela_temporaria()
        return True, taxa_confianca
    else:
        logging.warning("⚠️ Nenhuma lei atingiu a aderência mínima de 50% mesmo com filtro adaptativo. Limpando a staging da câmara.")
        limpar_tabela_temporaria()
        return False, "Nenhuma"

def limpar_tabela_temporaria():
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS analise_votos_temporaria")
        conn.commit()
        logging.info("🧹 [LIMPEZA] Tabela temporária 'analise_votos_temporaria' excluída com sucesso.")