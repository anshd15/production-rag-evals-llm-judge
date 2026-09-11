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


def embed(texts: list[str], cache_name: str | None = None) -> np.ndarray:
    """Return L2-normalised embeddings (so dot product == cosine similarity)."""
    if cache_name:
        key = hashlib.sha1("\n".join(texts).encode("utf-8")).hexdigest()[:12]
        path = CACHE_DIR / f"{cache_name}_{key}.npy"
        if path.exists():
            return np.load(path)
    vecs = _get_model().encode(texts, batch_size=128, normalize_embeddings=True,
                               show_progress_bar=False)
    vecs = vecs.astype(np.float32)
    if cache_name:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(path, vecs)
    return vecs
