# Arquivo: mini_esteira/vetorizar_lote.py
import os
import json
import logging
from google import genai
from dotenv import load_dotenv
from mini_esteira.mini_database import obter_conexao

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def vetorizar_proposicoes_faltantes():
    """
    Identifica proposições na tabela temporária que ainda não possuem vetor 
    no cache, gera os vetores em lotes de até 10 usando a API do Google,
    e armazena no cache_leis_vetorial.
    """
    if not API_KEY:
        logging.error("🛑 Chave GEMINI_API_KEY não configurada no .env.")
        return False

    # 1. Busca quais leis da tabela temporária não existem no nosso cache vetorial
    query_leis_sem_vetor = """
        SELECT t.id_proposicao, t.ementa 
        FROM analise_votos_temporaria t
        LEFT JOIN cache_leis_vetorial c ON t.id_proposicao = CAST(c.id_proposicao AS TEXT)
        WHERE c.id_proposicao IS NULL
    """
    
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute(query_leis_sem_vetor)
        leis_faltantes = cursor.fetchall()

    if not leis_faltantes:
        logging.info("✨ Todas as proposições selecionadas já possuem vetores em cache! Pulando etapa de vetorização.")
        return True

    logging.info(f"⏳ [VETORIZADOR EM LOTE] Identificadas {len(leis_faltantes)} leis sem vetor em cache. Iniciando geração...")

    # Inicializa o cliente GenAI do Google
    cliente_genai = genai.Client(api_key=API_KEY)
    
    # 2. Divide as leis pendentes em pacotes de até 50 elementos
    tamanho_lote = 50
    lotes = [leis_faltantes[i:i + tamanho_lote] for i in range(0, len(leis_faltantes), tamanho_lote)]
    total_gravado = 0

    for idx, lote in enumerate(lotes, 1):
        logging.info(f"📦 Processando lote {idx}/{len(lotes)} ({len(lote)} leis)...")
        
        # Prepara a lista de ementas higienizadas
        textos_para_vetorizar = [row[1] if row[1] and row[1].strip() else "Ementa não disponível" for row in lote]
        ids_lote = [int(row[0]) for row in lote]

        try:
            # Chama o Gemini 2 Embedding
            resposta = cliente_genai.models.embed_content(
                model='gemini-embedding-2',
                contents=textos_para_vetorizar
            )
            
            # Extrai os vetores retornados (Agora usando 'resposta' corrigido!)
            vetores_gerados = [emb.values for emb in resposta.embeddings]

            # Salva no cache_leis_vetorial
            with obter_conexao() as conn:
                cursor = conn.cursor()
                for id_prop, vetor in zip(ids_lote, vetores_gerados):
                    cursor.execute("""
                        INSERT OR REPLACE INTO cache_leis_vetorial (id_proposicao, vetor_json)
                        VALUES (?, ?)
                    """, (id_prop, json.dumps(vetor)))
                conn.commit()
                
            total_gravado += len(lote)
            
        except Exception as e:
            logging.error(f"❌ Erro ao processar lote {idx} na API: {e}")
            continue

    logging.info(f"✅ [VETORIZADOR EM LOTE] Concluído! {total_gravado} novos vetores armazenados em cache.")
    return True