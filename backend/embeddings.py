"""Local embedding model, loaded once and reused across requests.

Using a local sentence-transformer instead of a hosted embeddings API keeps
ingestion free and reproducible. See README's "Why These Choices" section
for the trade-offs.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_name)


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]
