# -*- coding: utf-8 -*-
"""Extração de transcrições do YouTube."""

from __future__ import annotations


def _transcricao_demo(video_id: str) -> list[dict]:
    return [
        {
            "text": f"Transcrição de demonstração do vídeo {video_id}.",
            "start": 0.0,
            "duration": 5.0,
        },
        {
            "text": "Este trecho representa uma fala parlamentar.",
            "start": 5.0,
            "duration": 6.0,
        },
    ]


def extrair_transcricao(
    video_id: str,
    idiomas: list[str] | None = None,
    vocabulario: list[str] | None = None,
    modo_demo: bool = True,
) -> list[dict]:
    if modo_demo or video_id.startswith("demo_"):
        return _transcricao_demo(video_id)

    idiomas = idiomas or ["pt-BR", "pt", "en"]

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise RuntimeError(
            "Instale youtube-transcript-api"
        ) from exc

    try:
        api = YouTubeTranscriptApi()
        resultado = api.fetch(video_id, languages=idiomas)

        return [
            {
                "text": trecho.text,
                "start": float(trecho.start),
                "duration": float(trecho.duration),
            }
            for trecho in resultado
        ]
    except Exception:
        return []
