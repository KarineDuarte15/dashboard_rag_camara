# Arquivo: src/vetorizacao/vetorizar_pergunta.py
import os
import json
import sqlite3
import logging
from google import genai
from dotenv import load_dotenv
from src.vetorizacao.mini_database import obter_conexao

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def obter_ou_criar_vetor_pergunta(texto_pergunta):
    texto_pergunta = texto_pergunta.strip()
    
    with obter_conexao() as conn:
        cursor = conn.cursor()
        
        # 1. TENTA BUSCAR NO HISTÓRICO PRIMEIRO
        cursor.execute(
            "SELECT id_pergunta, vetor_json FROM historico_consultas_vetorial WHERE LOWER(texto_pergunta) = LOWER(?)", 
            (texto_pergunta,)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            logging.info(f"🟢 [VETOR] Pergunta recuperada do cache local (ID: {resultado[0]}).")
            return resultado[0], json.loads(resultado[1])

        # 2. SE NÃO EXISTIR, ACIONA O GEMINI PARA GERAR
        if not client:
            logging.error("🛑 GEMINI_API_KEY não configurada no .env.")
            return None, None
            
        try:
            resposta = client.models.embed_content(
                model='gemini-embedding-2',
                contents=texto_pergunta
            )
            vetor = resposta.embeddings[0].values
            vetor_json = json.dumps(vetor)
            
            # 3. SALVA NO BANCO DE FORMA SEGURA
            cursor.execute("""
                INSERT OR REPLACE INTO historico_consultas_vetorial 
                (texto_pergunta, vetor_json, tema_classificado, data_consulta)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (texto_pergunta, vetor_json, ""))
            conn.commit()
            
            id_pergunta = cursor.lastrowid
            logging.info(f"🟢 [VETOR] Nova pergunta vetorizada e salva com o ID: {id_pergunta}")
            return id_pergunta, vetor

        except Exception as e:
            logging.error(f"❌ Erro ao vetorizar pergunta com o Gemini: {e}")
            return None, None