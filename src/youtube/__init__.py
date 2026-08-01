"""Pacote do pipeline perene de ingestão do YouTube."""

from .discovery import VideoMeta, get_discovery
from .state import StateStore, content_hash
from .transcript import extrair_transcricao

__all__ = [
    "StateStore",
    "VideoMeta",
    "content_hash",
    "extrair_transcricao",
    "get_discovery",
]
