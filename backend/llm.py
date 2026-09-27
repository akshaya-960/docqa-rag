"""Builds a grounded prompt from retrieved chunks and calls Gemini."""

import time

from google import genai
from google.genai import errors as genai_errors

from backend.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

_SYSTEM_PROMPT = """You are a precise question-answering assistant.
Answer the user's question using ONLY the context passages provided below.
If the context does not contain enough information to answer, say clearly
that you don't have enough information in the provided documents — do not
guess or use outside knowledge. Keep answers concise and cite which passage
number(s) you used, like [1], [2]."""


def build_context_block(chunks_with_docs) -> str:
    lines = []
    for i, (chunk, document) in enumerate(chunks_with_docs, start=1):
        lines.append(f"[{i}] (from {document.filename}, chunk {chunk.chunk_index})\n{chunk.content}")
    return "\n\n".join(lines)


def generate_answer(question: str, chunks_with_docs) -> str:
    if not chunks_with_docs:
        return "I don't have any ingested documents to answer from yet — try uploading one via /ingest first."

    context = build_context_block(chunks_with_docs)
    user_message = f"Context passages:\n\n{context}\n\nQuestion: {question}"

    # Gemini's free tier occasionally returns 503 "high demand" errors that
    # clear up within a second or two, so retry a couple of times before
    # giving up and surfacing a friendly message instead of a stack trace.
    last_error = None
    for attempt in range(3):
        try:
            response = _client.models.generate_content(
                model=settings.gemini_model,
                contents=user_message,
                config={"system_instruction": _SYSTEM_PROMPT},
            )
            return response.text
        except genai_errors.ServerError as e:
            last_error = e
            time.sleep(1.5 * (attempt + 1))

    return (
        "The AI model is temporarily overloaded (Gemini's free tier does this sometimes). "
        "Please try asking again in a moment."
    )