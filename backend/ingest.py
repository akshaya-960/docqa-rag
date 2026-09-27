"""Turn an uploaded file into stored, embedded chunks.

Chunking strategy is deliberately simple: fixed-size character windows with
overlap. It doesn't respect headings or paragraph structure (see README
Limitations) but is easy to reason about and good enough for a portfolio
corpus.
"""

import io

from pypdf import PdfReader
from sqlalchemy.orm import Session

from backend.config import settings
from backend.embeddings import embed_texts
from backend.models import Document, Chunk


def extract_text(filename: str, file_bytes: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    # Fall back to treating anything else as UTF-8 text.
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def ingest_file(db: Session, filename: str, file_bytes: bytes) -> tuple[Document, int]:
    text = extract_text(filename, file_bytes)
    pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)

    if not pieces:
        raise ValueError("No extractable text found in file")

    document = Document(filename=filename)
    db.add(document)
    db.flush()  # get document.id without committing yet

    vectors = embed_texts(pieces)
    for idx, (content, vector) in enumerate(zip(pieces, vectors)):
        db.add(
            Chunk(
                document_id=document.id,
                chunk_index=idx,
                content=content,
                embedding=vector,
            )
        )

    db.commit()
    db.refresh(document)
    return document, len(pieces)
