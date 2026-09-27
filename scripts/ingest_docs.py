"""Ingest every .pdf/.txt file in data/sample_docs/ in one go.

Usage:
    python scripts/ingest_docs.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal, init_db
from backend.ingest import ingest_file

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_docs"


def main():
    init_db()
    files = [f for f in SAMPLE_DIR.iterdir() if f.suffix.lower() in (".pdf", ".txt")]

    if not files:
        print(f"No .pdf/.txt files found in {SAMPLE_DIR}. Add some and re-run.")
        return

    db = SessionLocal()
    try:
        for f in files:
            document, count = ingest_file(db, f.name, f.read_bytes())
            print(f"Ingested {document.filename}: {count} chunks")
    finally:
        db.close()


if __name__ == "__main__":
    main()
