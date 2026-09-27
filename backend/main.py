"""FastAPI app: /health, /ingest, /ask."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.agent import choose_tool, run_calculator
from backend.database import init_db, get_db
from backend.ingest import ingest_file
from backend.llm import generate_answer
from backend.retrieval import retrieve_relevant_chunks
from backend.schemas import AskRequest, AskResponse, IngestResponse, SourceChunk


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="DocQA", version="0.1.0", lifespan=lifespan)

# Wide-open CORS is fine for a local portfolio project; a real deployment
# would restrict this to the actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")

    file_bytes = await file.read()
    try:
        document, chunk_count = ingest_file(db, file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return IngestResponse(document=document.filename, chunks_created=chunk_count)


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    tool = choose_tool(question)

    if tool == "calculator":
        return AskResponse(answer=run_calculator(question), used_tool="calculator", sources=[])

    chunks_with_docs = retrieve_relevant_chunks(db, question)
    answer = generate_answer(question, chunks_with_docs)
    sources = [
        SourceChunk(document=doc.filename, chunk_index=chunk.chunk_index, text=chunk.content)
        for chunk, doc in chunks_with_docs
    ]
    return AskResponse(answer=answer, used_tool="retrieval", sources=sources)
