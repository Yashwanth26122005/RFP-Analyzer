import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from src.rag_pipeline import answer_question, build_context


MOCK_CHUNKS = [
    {"text": "The system must support TLS 1.3 for all communications.", "source": "rfp.pdf", "page": 5, "chunk_id": "rfp_5_01", "score": 0.92},
    {"text": "Data must be encrypted at rest using AES-256.", "source": "rfp.pdf", "page": 7, "chunk_id": "rfp_7_01", "score": 0.88},
]


def test_build_context_format():
    ctx = build_context(MOCK_CHUNKS)
    assert "Page 5" in ctx
    assert "TLS 1.3" in ctx


def test_empty_question_returns_message():
    answer, sources = answer_question("")
    assert "Please enter" in answer
    assert sources == []


@patch("src.rag_pipeline.retrieve", return_value=[])
def test_no_chunks_returns_message(mock_retrieve):
    answer, sources = answer_question("What are the requirements?")
    assert "No relevant content" in answer
    assert sources == []


@patch("src.rag_pipeline.invoke_llm", return_value="TLS 1.3 is required for all communications.")
@patch("src.rag_pipeline.retrieve", return_value=MOCK_CHUNKS)
def test_answer_returned_with_sources(mock_retrieve, mock_llm):
    answer, sources = answer_question("What are the security requirements?")
    assert "TLS 1.3" in answer
    assert len(sources) > 0
    assert sources[0]["source"] == "rfp.pdf"


@patch("src.rag_pipeline.invoke_llm", side_effect=ConnectionError("Ollama not running"))
@patch("src.rag_pipeline.retrieve", return_value=MOCK_CHUNKS)
def test_llm_failure_returns_error_message(mock_retrieve, mock_llm):
    answer, sources = answer_question("What are the requirements?")
    assert "Ollama" in answer or "unavailable" in answer.lower() or "LLM" in answer
    assert sources == []
