from __future__ import annotations

import hashlib

from ingestor.pipeline import rodar_ciclo
from ingestor.state import StateStore


def gerar_channel_id_demo(nome_deputado: str) -> str:
    """Cria um identificador estável para o deputado no modo demo."""
    digest = hashlib.sha256(
        nome_deputado.strip().lower().encode("utf-8")
    ).hexdigest()[:12]

    return f"DEPUTADO_DEMO_{digest}"


def main() -> None:
    nome_deputado = input(
        "Informe o nome do deputado: "
    ).strip()

    temas_texto = input(
        "Informe os temas separados por vírgula: "
    ).strip()

    temas = [
        tema.strip()
        for tema in temas_texto.split(",")
        if tema.strip()
    ]

    if not nome_deputado:
        raise ValueError("O nome do deputado é obrigatório.")

    if not temas:
        raise ValueError("Informe pelo menos um tema.")

    canal = {
        "id": gerar_channel_id_demo(nome_deputado),
        "nome": nome_deputado,
        "handle": "@modo_demo",
        "vocabulario": temas,
    }

    config = {
        "modo_demo": True,
        "dominio": "youtube_deputados",
        "max_videos_por_ciclo": 3,
        "janela_descoberta_dias": 30,
        "idiomas_legenda": ["pt-BR", "pt", "en"],
        "vocabulario": temas,
    }

    store = StateStore(
        "datalake/control/teste_deputado.db"
    )

    print("\nExecutando pipeline em modo demo...")
    print(f"Deputado: {nome_deputado}")
    print(f"Temas: {temas}\n")

    resultado = rodar_ciclo(
        canal=canal,
        config=config,
        store=store,
    )

    resultado["deputado"] = nome_deputado
    resultado["temas"] = temas
    resultado["modo"] = "DEMO"

    print("\nResultado:")
    for chave, valor in resultado.items():
        print(f"- {chave}: {valor}")


if __name__ == "__main__":
    main()