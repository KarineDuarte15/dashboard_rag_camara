# -*- coding: utf-8 -*-
"""Persistência de estado, watermark, falhas e idempotência em SQLite."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


DDL = """
CREATE TABLE IF NOT EXISTS ingestion_state (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    dominio TEXT NOT NULL,
    published_at TEXT,
    title TEXT,
    status TEXT NOT NULL,
    content_hash TEXT,
    transcript_len INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    discovered_at TEXT NOT NULL,
    ingested_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS channel_watermark (
    channel_id TEXT PRIMARY KEY,
    last_published_at TEXT,
    last_run_at TEXT,
    videos_total INTEGER NOT NULL DEFAULT 0
);
"""


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


class StateStore:
    def __init__(self, db_path: str = "./datalake/control/ingestion.db") -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._conn() as conn:
            conn.executescript(DDL)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_watermark(self, channel_id: str) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT last_published_at
                FROM channel_watermark
                WHERE channel_id = ?
                """,
                (channel_id,),
            ).fetchone()

        return row["last_published_at"] if row else None

    def update_watermark(
        self,
        channel_id: str,
        published_at: str,
        novos: int,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO channel_watermark (
                    channel_id,
                    last_published_at,
                    last_run_at,
                    videos_total
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    last_published_at =
                        CASE
                            WHEN channel_watermark.last_published_at IS NULL
                                THEN excluded.last_published_at
                            WHEN excluded.last_published_at >
                                 channel_watermark.last_published_at
                                THEN excluded.last_published_at
                            ELSE channel_watermark.last_published_at
                        END,
                    last_run_at = excluded.last_run_at,
                    videos_total =
                        channel_watermark.videos_total +
                        excluded.videos_total
                """,
                (channel_id, published_at or "", _agora_iso(), int(novos)),
            )

    def ja_ingerido(self, video_id: str, novo_hash: str | None = None) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT status, content_hash
                FROM ingestion_state
                WHERE video_id = ?
                """,
                (video_id,),
            ).fetchone()

        if not row or row["status"] != "INGESTED":
            return False

        if novo_hash is not None and row["content_hash"] != novo_hash:
            return False

        return True

    def marcar_descoberto(
        self,
        video_id: str,
        channel_id: str,
        dominio: str,
        published_at: str,
        title: str,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO ingestion_state (
                    video_id,
                    channel_id,
                    dominio,
                    published_at,
                    title,
                    status,
                    discovered_at
                )
                VALUES (?, ?, ?, ?, ?, 'DISCOVERED', ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    dominio = excluded.dominio,
                    published_at = excluded.published_at,
                    title = excluded.title
                """,
                (
                    video_id,
                    channel_id,
                    dominio,
                    published_at,
                    title,
                    _agora_iso(),
                ),
            )

    def marcar_ingerido(
        self,
        video_id: str,
        c_hash: str,
        t_len: int,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE ingestion_state
                SET status = 'INGESTED',
                    content_hash = ?,
                    transcript_len = ?,
                    ingested_at = ?,
                    attempts = attempts + 1,
                    error = NULL
                WHERE video_id = ?
                """,
                (c_hash, int(t_len), _agora_iso(), video_id),
            )

    def marcar_falha(self, video_id: str, erro: object) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE ingestion_state
                SET status = 'FAILED',
                    error = ?,
                    attempts = attempts + 1
                WHERE video_id = ?
                """,
                (str(erro)[:300], video_id),
            )
