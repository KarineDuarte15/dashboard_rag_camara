import sqlite3
import pandas as pd
from google import genai
import uuid
import time # <-- 1. IMPORTAMOS A BIBLIOTECA DE TEMPO AQUI

from cruzamento_dados import processar_cruzamento

API_KEY = "AIzaSyCQH7i2h9q0ejmtkTIBQaSv1E8_WgYy1LY" 
cliente_genai = genai.Client(api_key=API_KEY)

def executar_assistente_legislativo():
    nome_banco = 'camara_dados.db'
    
    try:
        conn = sqlite3.connect(nome_banco)
        df_lista_temas = pd.read_sql_query("SELECT DISTINCT tema FROM temas_proposicoes", conn)
        temas_disponiveis = df_lista_temas['tema'].dropna().tolist()
        conn.close()
    except Exception as e:
        print(f"Erro ao acessar banco de dados inicial: {e}")
        return

    print("="*50)
    print("ASSISTENTE DE ANÁLISE LEGISLATIVA")
    print("="*50)
    
    nome_deputado_input = input("1. Digite o nome do deputado (ex: SILVIA CUNHA): ").strip().upper()
    pergunta_usuario = input("2. Qual a sua pergunta sobre as votações? \n > ").strip()

    id_da_pergunta = str(uuid.uuid4().hex) 
    print(f"\n[Sessão de usuário criada: {id_da_pergunta}]")

    print("Processando a sua pergunta via IA...")

    prompt_ia = f"""
    Abaixo está uma pergunta feita por um usuário sobre projetos de lei:
    "{pergunta_usuario}"
    
    Abaixo está a lista de temas oficiais registrados no banco de dados da Câmara:
    {temas_disponiveis}
    
    Identifique qual ou quais temas dessa lista melhor correspondem à pergunta.
    Responda APENAS com os nomes exatos dos temas separados por vírgula. Não adicione texto extra.
    """
    
    # =========================================================
    # 2. SISTEMA DE RETENTATIVA DA IA (RETRY COM DELAY DE 20s)
    # =========================================================
    max_tentativas = 3
    tentativa_atual = 1
    
    while tentativa_atual <= max_tentativas:
        try:
            resposta_ia = cliente_genai.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt_ia
            )
            temas_identificados = [t.strip(" .\n'\"") for t in resposta_ia.text.split(',')]
            print(f"[IA identificou os temas]: {temas_identificados}")
            
            break # SUCESSO! A palavra "break" quebra o loop e ele continua o código normal
            
        except Exception as e:
            print(f"\n[!] Erro de tráfego na API Gemini (Tentativa {tentativa_atual}/{max_tentativas}): {e}")
            
            if tentativa_atual < max_tentativas:
                print("Aguardando 20 segundos para tentar novamente...\n")
                time.sleep(20) # PAUSA O SCRIPT POR 20 SEGUNDOS
                tentativa_atual += 1
            else:
                print("A API está muito instável no momento. Limite de tentativas atingido. Tente novamente mais tarde.")
                return # Encerra o script pois falhou 3 vezes seguidas

    # =========================================================
    # 3. ENVIANDO PARA O MOTOR APÓS SUCESSO
    # =========================================================
    processar_cruzamento(
        nome_deputado_input=nome_deputado_input, 
        pergunta_usuario=pergunta_usuario, 
        temas_identificados=temas_identificados, 
        nome_banco=nome_banco,
        id_pergunta=id_da_pergunta 
    )

if __name__ == "__main__":
    executar_assistente_legislativo()