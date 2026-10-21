"""Embeddings for the guardrail, tool routing, Simple RAG and the seeded documents.

Everything runs locally with a sentence-transformers model, so the demo needs no embeddings API key
(the chat model is not used for embeddings). The default model is small (384 dimensions) and is downloaded from
Hugging Face on first use, then cached.

Settings:
    EMBEDDING_MODEL  sentence-transformers model name, or "hash" for deterministic fake vectors
                     (tests and offline use only; they carry no meaning)
    EMBEDDING_DIM    must match the model. Vector fields in every domain schema use this size, so
                     after changing it run `make generate-models` and `make setup`.
"""

from __future__ import annotations

import asyncio
import hashlib
import threading
from functools import lru_cache
from typing import Any

from backend.app.settings import get_settings

EMBEDDING_DIM = get_settings().embedding_dim
HASH_MODEL = "hash"
_load_lock = threading.Lock()


def _hash_vector(text: str, dim: int) -> list[float]:
    """Deterministic pseudo-embedding: same text gives the same vector. Not semantic."""
    values: list[float] = []
    counter = 0
    while len(values) < dim:
        digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        values.extend((byte / 127.5) - 1.0 for byte in digest)
        counter += 1
    vector = values[:dim]
    norm = sum(v * v for v in vector) ** 0.5 or 1.0
    return [v / norm for v in vector]


@lru_cache(maxsize=1)
def get_vectorizer() -> Any:
    """The RedisVL vectorizer used for every embedding (also handed to semantic routers)."""
    settings = get_settings()
    with _load_lock:
        if settings.embedding_model == HASH_MODEL:
            from redisvl.utils.vectorize import CustomTextVectorizer

            dim = settings.embedding_dim
            return CustomTextVectorizer(
                embed=lambda text, **_: _hash_vector(text, dim),
                embed_many=lambda texts, **_: [_hash_vector(t, dim) for t in texts],
            )
        from redisvl.utils.vectorize import HFTextVectorizer

        vectorizer = HFTextVectorizer(model=settings.embedding_model)
        if vectorizer.dims != settings.embedding_dim:
            raise RuntimeError(
                f"EMBEDDING_DIM={settings.embedding_dim} but {settings.embedding_model} produces "
                f"{vectorizer.dims}-dimensional vectors. Set EMBEDDING_DIM={vectorizer.dims}, then run "
                "`make generate-models` and `make setup` so the vector fields and stored data match."
            )
        return vectorizer


def embed_query(text: str) -> list[float]:
    return list(get_vectorizer().embed(text))


def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [list(v) for v in get_vectorizer().embed_many(texts)]


async def aembed_query(text: str) -> list[float]:
    """Embed without blocking the event loop (model inference is CPU work)."""
    return await asyncio.to_thread(embed_query, text)
