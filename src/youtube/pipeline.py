# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

from .discovery import get_discovery
from .state import StateStore, content_hash
from .transcript import extrair_transcricao


log = logging.getLogger("ingestor")


SILVER_SCHEMA = DataFrameSchema(
    {
        "video_id": Column(str, nullable=False),
        "ordem": Column(int, Check.ge(0)),
        "texto": Column(str, Check.str_length(min_value=1)),
        "inicio_seg": Column(float, Check.ge(0)),
        "duracao_seg": Column(float, Check.gt(0)),
    },
    coerce=True,
)


def salvar_bronze(video_id: str, trechos: list[dict]) -> None:
    dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pasta = Path(f"datalake/bronze/dominio=youtube/dt={dia}")
    pasta.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(trechos).to_json(
        pasta / f"{video_id}.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )


def gerar_silver(video_id: str, trechos: list[dict]) -> pd.DataFrame:
    registros = [
        {
            "video_id": video_id,
            "ordem": ordem,
            "texto": str(trecho["text"]).strip(),
            "inicio_seg": float(trecho["start"]),
            "duracao_seg": float(trecho["duration"]),
        }
        for ordem, trecho in enumerate(trechos)
    ]

    df = pd.DataFrame(registros)
    return SILVER_SCHEMA.validate(df)


def salvar_silver(video_id: str, df: pd.DataFrame) -> None:
    dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pasta = Path(f"datalake/silver/dominio=youtube/dt={dia}")
    pasta.mkdir(parents=True, exist_ok=True)

    df.to_parquet(pasta / f"{video_id}.parquet", index=False)


def gerar_gold() -> pd.DataFrame:
    arquivos = list(Path("datalake/silver").glob("**/*.parquet"))

    if not arquivos:
        return pd.DataFrame()

    silver = pd.concat(
        [pd.read_parquet(arquivo) for arquivo in arquivos],
        ignore_index=True,
    )

    gold = (
        silver.groupby("video_id")
        .agg(
            quantidade_trechos=("ordem", "count"),
            texto_completo=("texto", " ".join),
        )
        .reset_index()
    )

    pasta = Path("datalake/gold/dominio=youtube")
    pasta.mkdir(parents=True, exist_ok=True)

    gold.to_parquet(
        pasta / "resumo_videos.parquet",
        index=False,
    )

    return gold


def rodar_ciclo(
    canal: dict,
    config: dict,
    store: StateStore,
) -> dict:
    descobertos = 0
    ingeridos = 0
    pulados = 0
    falhas = 0

    channel_id = canal["id"]
    nome_canal = canal["nome"]
    dominio = config.get("dominio", "youtube")
    vocabulario = canal.get(
        "vocabulario",
        config.get("vocabulario", []),
    )

    watermark = store.get_watermark(channel_id)

    discovery = get_discovery(
        modo_demo=bool(config.get("modo_demo", True)),
        api_key=config.get("youtube_api_key"),
    )

    videos = discovery.descobrir(
        channel_id=channel_id,
        since_iso=watermark,
        max_videos=int(config.get("max_videos_por_ciclo", 5)),
        janela_dias=int(config.get("janela_descoberta_dias", 30)),
    )

    maior_data = watermark or ""

    for video in videos:
        descobertos += 1

        store.marcar_descoberto(
            video_id=video.video_id,
            channel_id=channel_id,
            dominio=dominio,
            published_at=video.published_at,
            title=video.title,
        )

        try:
            trechos = extrair_transcricao(
                video_id=video.video_id,
                idiomas=config.get(
                    "idiomas_legenda",
                    ["pt-BR", "pt", "en"],
                ),
                vocabulario=vocabulario,
                modo_demo=bool(config.get("modo_demo", True)),
            )

            if not trechos:
                store.marcar_falha(
                    video.video_id,
                    "sem transcrição",
                )
                falhas += 1
                continue

            texto_total = " ".join(
                trecho["text"] for trecho in trechos
            )
            hash_atual = content_hash(texto_total)

            if store.ja_ingerido(video.video_id, hash_atual):
                pulados += 1
                continue

            salvar_bronze(video.video_id, trechos)

            df_silver = gerar_silver(
                video.video_id,
                trechos,
            )
            salvar_silver(video.video_id, df_silver)

            store.marcar_ingerido(
                video.video_id,
                hash_atual,
                len(df_silver),
            )

            ingeridos += 1
            maior_data = max(
                maior_data,
                video.published_at or "",
            )

        except Exception as erro:
            store.marcar_falha(video.video_id, erro)
            falhas += 1
            log.exception(
                "Erro ao processar vídeo %s",
                video.video_id,
            )

    gold = gerar_gold()

    if ingeridos > 0 and maior_data:
        store.update_watermark(
            channel_id,
            maior_data,
            ingeridos,
        )

    resultado = {
        "canal": nome_canal,
        "channel_id": channel_id,
        "videos_descobertos": descobertos,
        "videos_ingeridos": ingeridos,
        "pulados_idempotencia": pulados,
        "falhas": falhas,
        "registros_gold": len(gold),
    }

    log.info("Ciclo concluído: %s", resultado)
    return resultado
