# -*- coding: utf-8 -*-
"""Descoberta incremental de vídeos por canal."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class VideoMeta:
    video_id: str
    channel_id: str
    title: str
    published_at: str


class YouTubeDiscovery:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")

        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY não configurada")

        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "Instale google-api-python-client"
            ) from exc

        self.youtube = build(
            "youtube",
            "v3",
            developerKey=self.api_key,
            cache_discovery=False,
        )

    def _uploads_playlist(self, channel_id: str) -> str:
        resposta = (
            self.youtube.channels()
            .list(part="contentDetails", id=channel_id)
            .execute()
        )

        itens = resposta.get("items", [])
        if not itens:
            raise ValueError(f"Canal não encontrado: {channel_id}")

        return itens[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def descobrir(
        self,
        channel_id: str,
        since_iso: str | None,
        max_videos: int,
        janela_dias: int,
    ) -> list[VideoMeta]:
        playlist_id = self._uploads_playlist(channel_id)
        limite = max(1, min(int(max_videos), 50))
        corte = datetime.now(timezone.utc) - timedelta(days=int(janela_dias))

        resposta = (
            self.youtube.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=limite,
            )
            .execute()
        )

        videos: list[VideoMeta] = []

        for item in resposta.get("items", []):
            detalhes = item.get("contentDetails", {})
            snippet = item.get("snippet", {})
            publicada = detalhes.get("videoPublishedAt", "")

            if since_iso and publicada <= since_iso:
                continue

            if publicada and publicada < corte.isoformat():
                continue

            videos.append(
                VideoMeta(
                    video_id=detalhes["videoId"],
                    channel_id=channel_id,
                    title=snippet.get("title", ""),
                    published_at=publicada,
                )
            )

        return videos


class DemoDiscovery:
    def descobrir(
        self,
        channel_id: str,
        since_iso: str | None,
        max_videos: int,
        janela_dias: int,
    ) -> list[VideoMeta]:
        agora = datetime.now(timezone.utc)

        return [
            VideoMeta(
                video_id=f"demo_{channel_id[-4:]}_{indice}",
                channel_id=channel_id,
                title=f"Vídeo de demonstração {indice}",
                published_at=(agora - timedelta(hours=indice)).isoformat(),
            )
            for indice in range(1, int(max_videos) + 1)
        ]


def get_discovery(modo_demo: bool, api_key: str | None = None):
    if modo_demo:
        return DemoDiscovery()

    return YouTubeDiscovery(api_key=api_key)
