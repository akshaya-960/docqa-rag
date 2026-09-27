"""API tests. The LLM call and embedding model are mocked so tests run fast
and don't require a real API key or model download.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_calculator_tool_routes_without_llm_call():
    response = client.post("/ask", json={"question": "12 + 5"})
    assert response.status_code == 200
    body = response.json()
    assert body["used_tool"] == "calculator"
    assert "17" in body["answer"]


def test_ask_empty_question_is_rejected():
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 400


@patch("backend.main.retrieve_relevant_chunks", return_value=[])
def test_ask_with_no_ingested_documents(mock_retrieve):
    response = client.post("/ask", json={"question": "What is in the handbook?"})
    assert response.status_code == 200
    body = response.json()
    assert body["used_tool"] == "retrieval"
    assert "don't have any ingested documents" in body["answer"]


def test_ingest_rejects_unsupported_file_type():
    response = client.post(
        "/ingest",
        files={"file": ("notes.docx", b"fake content", "application/octet-stream")},
    )
    assert response.status_code == 400
