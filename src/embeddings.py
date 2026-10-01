"""Sentence embeddings with an on-disk cache (so re-runs don't re-embed 30k texts)."""
import hashlib

import numpy as np

from src.config import PROCESSED

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = PROCESSED / "emb_cache"
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model


class IndexMissing(RuntimeError):
    """The precomputed embedding cache this caller requires is not on disk."""


def embed(texts: list[str], cache_name: str | None = None,
          require_cache: bool = False) -> np.ndarray:
    """Return L2-normalised embeddings (so dot product == cosine similarity).

    `require_cache` turns a miss into an error instead of a silent recompute. A
    33,838-row miss takes minutes, prints nothing and raises nothing, which in a
    served request is indistinguishable from a hang -- and is exactly how the
    first Cloud Run deploy failed, because .dockerignore kept the index out of
    the image. A caller that cannot afford to rebuild should say so and fail at
    startup instead of stalling mid-request.
    """
    if cache_name:
        key = hashlib.sha1("\n".join(texts).encode("utf-8")).hexdigest()[:12]
        path = CACHE_DIR / f"{cache_name}_{key}.npy"
        if path.exists():
            return np.load(path)
        if require_cache:
            raise IndexMissing(
                f"{path.name} is missing ({len(texts)} texts). Rebuilding it here would take "
                f"minutes and silently stall the caller. Ship the embedding cache with the "
                f"image, or pass require_cache=False to rebuild deliberately.")
    vecs = _get_model().encode(texts, batch_size=128, normalize_embeddings=True,
                               show_progress_bar=False)
    vecs = vecs.astype(np.float32)
    if cache_name:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(path, vecs)
    return vecs
