"""Pydantic models for API request/response bodies."""

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    document: str
    chunk_index: int
    text: str


class AskResponse(BaseModel):
    answer: str
    used_tool: str  # "retrieval" or "calculator"
    sources: list[SourceChunk] = []


class IngestResponse(BaseModel):
    document: str
    chunks_created: int
