# Arquivo: src/semantic_router/input_usuario.py
import sqlite3
import pandas as pd
from google import genai
import time
import os
from dotenv import load_dotenv

# Import ajustado para a nova estrutura de pastas
from src.camara.cruzamento_dados import processar_cruzamento

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
cliente_genai = genai.Client(api_key=API_KEY) if API_KEY else None

def executar_assistente_legislativo(nome_deputado, pergunta_usuario, id_da_pergunta):
    if not cliente_genai:
        print("❌ Chave GEMINI_API_KEY não encontrada no arquivo .env!")
        return False

    nome_banco = 'camara_dados.db'

    try:
        conn = sqlite3.connect(nome_banco)
        df_lista_temas = pd.read_sql_query("SELECT DISTINCT tema FROM temas_proposicoes", conn)
        temas_disponiveis = df_lista_temas['tema'].dropna().tolist()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao acessar banco de dados inicial: {e}")
        return False

    print("\n🧠 Processando a sua pergunta via IA (Buscando Temas)...")

    prompt_ia = f"""
    Abaixo está uma pergunta feita por um usuário sobre projetos de lei:
    "{pergunta_usuario}"
    
    Abaixo está a lista de temas oficiais registrados no banco de dados da Câmara:
    {temas_disponiveis}
    
    Selecione exatamente os 3 temas oficiais da lista acima que possuam maior relação com a pergunta do usuário.
    Responda APENAS com os nomes exatos desses 3 temas separados por vírgula. Não adicione introduções, explicações ou qualquer texto extra.
    """
    
    max_tentativas = 3
    tentativa_atual = 1
    
    while tentativa_atual <= max_tentativas:
        try:
            resposta_ia = cliente_genai.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=prompt_ia
            )
            temas_identificados = [t.strip(" .\n'\"") for t in resposta_ia.text.split(',')]
            print(f"✅ [IA identificou os temas]: {temas_identificados}")
            break 
            
        except Exception as e:
            print(f"\n⚠️ Erro de tráfego na API Gemini (Tentativa {tentativa_atual}/{max_tentativas}): {e}")
            if tentativa_atual < max_tentativas:
                print("⏳ Aguardando 20 segundos para tentar novamente...\n")
                time.sleep(20)
                tentativa_atual += 1
            else:
                print("❌ A API está muito instável no momento. Limite atingido.")
                return False 

    # Chama o cruzamento do André (Staging)
    sucesso_cruzamento = processar_cruzamento(
        nome_deputado_input=nome_deputado, 
        pergunta_usuario=pergunta_usuario, 
        temas_identificados=temas_identificados, 
        id_pergunta=id_da_pergunta,
        nome_banco=nome_banco
    )
    
    return sucesso_cruzamento