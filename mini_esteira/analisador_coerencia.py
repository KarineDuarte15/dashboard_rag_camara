# Arquivo: mini_esteira/analisador_coerencia.py
import os
import json
import sqlite3
import logging
from datetime import datetime  # ⚠️ CORREÇÃO: Importação essencial que estava faltando!
from google import genai
from dotenv import load_dotenv
from mini_esteira.mini_database import obter_conexao

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def gerar_auditoria_coerencia(nome_deputado, pergunta_tema):
    """
    Busca dados consolidados da Gold no SQLite, envia ao Gemini para avaliar
    coerência de postura política e salva o veredito final em uma tabela Gold de auditoria.
    """
    if not client:
        logging.error("🛑 GEMINI_API_KEY não configurada no .env.")
        return None

    logging.info(f"🤖 [IA AUDITORA] Iniciando análise de coerência para {nome_deputado}...")

    # 1. Carrega dados consolidados das tabelas Gold
    with obter_conexao() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        votos = cursor.execute(
            "SELECT id_proposicao, ementa, tipoVoto FROM votos_gold_youtube WHERE UPPER(nome_deputado) LIKE ?", 
            (f"%{nome_deputado.upper()}%",)
        ).fetchall()
        
        videos = cursor.execute(
            "SELECT video_id, texto_completo FROM transcricoes_gold_youtube WHERE UPPER(deputado) LIKE ?", 
            (f"%{nome_deputado.upper()}%",)
        ).fetchall()

    if not votos and not videos:
        logging.warning("⚠️ Dados insuficientes no banco para realizar o cruzamento.")
        return None

    # 2. Formata os dados para o Prompt
    discursos_consolidados = "\n".join([f"- Vídeo {v['video_id']}: {v['texto_completo']}" for v in videos])
    votos_consolidados = "\n".join([f"- PL {v['id_proposicao']} (Voto: {v['tipoVoto']}): {v['ementa']}" for v in votos])

    prompt = f"""
    Você é um analista político sênior especializado em auditoria de discursos parlamentares.
    Sua tarefa é analisar a coerência entre o DISCURSO (o que o deputado falou no YouTube) e a PRÁTICA (como ele votou nos projetos de lei na Câmara dos Deputados) sobre o tema: "{pergunta_tema}".

    DADOS DO DISCURSO (YouTube):
    {discursos_consolidados if discursos_consolidados else "Nenhum discurso registrado no banco."}

    DADOS DA PRÁTICA (Câmara - Votos reais):
    {votos_consolidados if votos_consolidados else "Nenhum voto registrado no banco."}

    Por favor, faça uma análise detalhada comparando os dois lados. Em seguida, determine:
    1. Um Score de Contradição de 0 a 100 (onde 0% é totalmente coerente e 100% é totalmente contraditório).
    2. Um resumo executivo claro, imparcial e direto da análise.
    3. Evidências textuais do discurso confrontando as votações na Câmara.

    Responda EXCLUSIVAMENTE em formato JSON estruturado com as seguintes chaves (sem blocos Markdown adicionais):
    {{
        "score_contradicacao": <inteiro entre 0 e 100>,
        "resumo": "<texto explicativo>",
        "evidencias": [
            {{"discurso": "<trecho falado>", "pratica": "<voto/proposição>", "conclusao": "<explicacao da discrepância>"}}
        ]
    }}
    """

    try:
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        dados_json = json.loads(resposta.text)

        # 3. Salva o veredito final na tabela Gold de Auditoria de Coerência
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relatorio_coerencia_gold (
                    deputado TEXT PRIMARY KEY,
                    pergunta TEXT,
                    score_contradicacao INTEGER,
                    resumo TEXT,
                    evidencias_json TEXT,
                    data_analise TEXT
                )
            """)
            cursor.execute("""
                INSERT OR REPLACE INTO relatorio_coerencia_gold 
                (deputado, pergunta, score_contradicacao, resumo, evidencias_json, data_analise)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                nome_deputado,
                pergunta_tema,
                dados_json["score_contradicacao"],
                dados_json["resumo"],
                json.dumps(dados_json["evidencias"]),
                datetime.now().isoformat()
            ))
            conn.commit()
            
        logging.info("🥇 [IA AUDITORA] Relatório de coerência salvo com sucesso na Gold!")
        return dados_json

    except Exception as e:
        logging.error(f"❌ Erro ao processar auditoria de coerência: {e}")
        return None