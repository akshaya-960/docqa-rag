"""Similarity search over stored chunks using pgvector's cosine distance."""

from sqlalchemy.orm import Session

from backend.config import settings
from backend.embeddings import embed_text
from backend.models import Chunk, Document


def retrieve_relevant_chunks(db: Session, question: str, top_k: int | None = None):
    """Return the top-k most similar chunks (with their parent document) to `question`.

    pgvector's `<=>` operator computes cosine distance directly in SQL, so the
    ranking happens in the database rather than pulling every row into Python.
    """
    top_k = top_k or settings.top_k
    query_vector = embed_text(question)

    results = (
        db.query(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .order_by(Chunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
        .all()
    )
    return results
