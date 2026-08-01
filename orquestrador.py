# Arquivo: orquestrador.py
import hashlib
import logging
import time
import sqlite3
import pandas as pd
from pathlib import Path

# --- Módulos de vetorização e cache (src/vetorizacao) ---
from src.vetorizacao.mini_database import inicializar_mini_banco
from src.vetorizacao.vetorizar_pergunta import obter_ou_criar_vetor_pergunta
from src.vetorizacao.vetorizar_lote import vetorizar_proposicoes_faltantes

# --- Módulo de busca vetorial / RAG (src/rag) ---
from src.rag.comparar_vetores import executar_ranking_comparacao

# --- Módulo de roteamento semântico + ETL da Câmara (src/semantic_router) ---
from src.semantic_router.input_usuario import executar_assistente_legislativo

# --- Módulo de ingestão do YouTube (src/youtube) ---
from src.youtube.pipeline import rodar_ciclo
from src.youtube.state import StateStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def gerar_channel_id_demo(nome_deputado: str) -> str:
    """Cria um identificador estável para o deputado no modo demo."""
    digest = hashlib.sha256(
        nome_deputado.strip().lower().encode("utf-8")
    ).hexdigest()[:12]

    return f"DEPUTADO_DEMO_{digest}"

def executar_pipeline_mestre(nome_deputado, pergunta_usuario, callback_progresso=None):
    """
    Executa o pipeline completo de cruzamento de dados.
    Suporta callback_progresso(mensagem, porcentagem) para atualizar o Streamlit em tempo real.
    """
    # Função interna para centralizar os logs e atualizar a tela do Streamlit ao mesmo tempo
    def notificar(mensagem, progresso_percentual):
        logging.info(mensagem)
        if callback_progresso:
            callback_progresso(mensagem, progresso_percentual)

    print("\n" + "="*75)
    notificar("🚦 INICIANDO PIPELINE INTEGRADO MESTRE: CÂMARA 🏛️ + YOUTUBE 🎥", 5)
    print("="*75)

    # 1. Garante a estrutura do banco principal
    inicializar_mini_banco()
    nome_banco_unificado = 'camara_dados.db'

    nome_deputado = nome_deputado.strip().upper()
    pergunta_usuario = pergunta_usuario.strip()

    if not nome_deputado or not pergunta_usuario:
        notificar("⚠️ Dados incompletos. Pipeline abortado.", 0)
        return False

    tempo_inicio = time.time()

    # =========================================================================
    # FASE 1: PROCESSAMENTO CÂMARA (Lincoln & André)
    # =========================================================================
    notificar("⏳ [FASE CÂMARA - 1/3] Vetorizando a pergunta no histórico...", 15)
    id_pergunta, _ = obter_ou_criar_vetor_pergunta(pergunta_usuario)

    if not id_pergunta:
        notificar("🛑 Falha ao vetorizar a pergunta. Abortando.", 0)
        return False

    notificar("⏳ [FASE CÂMARA - 2/3] Acionando classificação de temas e cruzamentos...", 30)
    sucesso_etl = executar_assistente_legislativo(
        nome_deputado=nome_deputado,
        pergunta_usuario=pergunta_usuario,
        id_da_pergunta=id_pergunta
    )

    if not sucesso_etl:
        notificar("🛑 O ETL de staging da Câmara falhou. Encerrando.", 0)
        return False

    notificar("⏳ [FASE CÂMARA - 3/3] Vetorizando ementas e gerando Camada Gold da Câmara...", 45)
    vetorizar_proposicoes_faltantes()
    
    # Captura a taxa de confiança adaptativa calculada pela IA
    sucesso_ranking, confianca_ranking = executar_ranking_comparacao(id_pergunta_alvo=id_pergunta)

    # Recarrega os temas identificados pela IA de forma segura contra NoneType
    conn = sqlite3.connect(nome_banco_unificado)
    cursor = conn.cursor()
    cursor.execute("SELECT tema_classificado FROM historico_consultas_vetorial WHERE id_pergunta = ?", (id_pergunta,))
    res = cursor.fetchone()
    conn.close()
    
    temas_str = res[0] if (res and res[0] is not None) else ""
    
    if not temas_str:
        notificar("⚠️ Campo 'tema_classificado' vazio. Aplicando vocabulário de segurança.", 50)
        temas_tags = ["votação", "PL", "projeto de lei", "deputado"]
    else:
        temas_tags = [t.strip() for t in temas_str.split(',') if t.strip()]

    # =========================================================================
    # FASE 2: INGESTÃO DO YOUTUBE (Lucas)
    # =========================================================================
    print("\n" + "-"*75)
    notificar(f"⏳ [FASE YOUTUBE] Inicializando Ingestor do YouTube para: {nome_deputado}", 60)
    print("-"*75)

    canal_mock = {
        "id": gerar_channel_id_demo(nome_deputado),
        "nome": nome_deputado,
        "handle": "@modo_demo",
        "vocabulario": temas_tags,
    }

    config_mock = {
        "modo_demo": True, 
        "dominio": "youtube_deputados",
        "max_videos_por_ciclo": 5,
        "janela_descoberta_dias": 30,
        "idiomas_legenda": ["pt-BR", "pt"],
        "vocabulario": temas_tags,
    }

    store_unificado = StateStore(nome_banco_unificado)

    try:
        resultado_youtube = rodar_ciclo(
            canal=canal_mock,
            config=config_mock,
            store=store_unificado,
        )
        notificar("✅ [YOUTUBE OK] Ingestão finalizada!", 70)
        
        # =====================================================================
        # PONTE DE INTEGRAÇÃO: PARQUET -> SQLITE
        # =====================================================================
        path_parquet = Path("datalake/gold/dominio=youtube/resumo_videos.parquet")
        
        if path_parquet.exists():
            notificar("💾 [INTEGRAÇÃO] Convertendo a Camada Gold (Parquet) do YouTube para o SQLite...", 80)
            df_youtube_gold = pd.read_parquet(path_parquet)
            df_youtube_gold['deputado'] = nome_deputado
            
            conn = sqlite3.connect(nome_banco_unificado)
            df_youtube_gold.to_sql('transcricoes_gold_youtube', conn, if_exists='replace', index=False)
            conn.close()
            notificar("🥇 [INTEGRAÇÃO OK] Tabela 'transcricoes_gold_youtube' alimentada!", 85)
        else:
            notificar("⚠️ Arquivo Parquet da Gold do YouTube não foi localizado.", 85)

    except Exception as e:
        notificar(f"❌ Erro ao rodar o pipeline do YouTube: {e}", 85)

   # =========================================================================
    # FASE 3: AUDITORIA MESTRE DE COERÊNCIA (IA Cruzada)
    # =========================================================================
    print("\n" + "-"*75)
    notificar("⏳ [FASE COERÊNCIA] Iniciando cruzamento e RAG analítico pelo Gemini...", 90)
    print("-"*75)
    
    from src.rag.analisador_coerencia import gerar_auditoria_coerencia
    
    # CORREÇÃO: Ajustado o nome do parâmetro para bater com o analisador
    auditoria_resultado = gerar_auditoria_coerencia(
        nome_deputado=nome_deputado, 
        pergunta_tema=pergunta_usuario
    )
    
    tempo_total = round(time.time() - tempo_inicio, 2)
    print("\n" + "="*75)
    notificar(f"🏁 PIPELINE EXECUTADO COM SUCESSO EM {tempo_total}s!", 100)
    print("="*75 + "\n")

    return True

# Mantém a compatibilidade para rodar direto pelo terminal caso queira testar isolado
if __name__ == "__main__":
    print("\n📝 PREENCHA OS DADOS DA BUSCA VIA TERMINAL")
    nome = input("Digite o nome do deputado (ex: TIRIRICA): ")
    pergunta = input("Qual a sua pergunta sobre os projetos de lei? \n> ")
    executar_pipeline_mestre(nome, pergunta)