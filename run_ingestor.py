# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from ingestor.pipeline import rodar_ciclo
from ingestor.state import StateStore

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def carregar_config() -> dict:
    caminho = Path("config/canais.yaml")

    with caminho.open("r", encoding="utf-8") as arquivo:
        config = yaml.safe_load(arquivo) or {}

    config.setdefault("modo_demo", True)
    config.setdefault("max_videos_por_ciclo", 5)
    config.setdefault("janela_descoberta_dias", 30)
    config.setdefault(
        "idiomas_legenda",
        ["pt-BR"],
    )
    config.setdefault(
        "caminho_sqlite",
        "datalake/control/ingestion.db",
    )

    config["youtube_api_key"] = os.getenv(
        "YOUTUBE_API_KEY"
    )

    if not config["modo_demo"] and not config["youtube_api_key"]:
        raise ValueError(
            "Modo real ativado, mas YOUTUBE_API_KEY não foi encontrada no .env"
        )

    return config


def main() -> None:
    config = carregar_config()
    canais = config.get("canais", [])

    if not canais:
        raise ValueError(
            "Nenhum canal configurado em config/canais.yaml"
        )

    store = StateStore(
        config["caminho_sqlite"]
    )

    resultados = []

    for canal in canais:
        print(f"\nProcessando: {canal['nome']}")

        resultado = rodar_ciclo(
            canal=canal,
            config=config,
            store=store,
        )

        resultados.append(resultado)
        print(resultado)

    print("\nPipeline finalizado.")
    print(f"Canais processados: {len(resultados)}")


if __name__ == "__main__":
    main()