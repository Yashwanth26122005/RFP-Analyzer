from typing import List, Dict, Optional, Tuple
from src.retriever import retrieve
from src.llm import invoke_llm
from src.prompts import QA_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def build_context(chunks: List[Dict]) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c['source']}, Page {c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)

def answer_question(question: str, source_filter: Optional[str] = None) -> Tuple[str, List[Dict]]:
    """Run RAG pipeline: retrieve → build context → LLM → return answer + sources."""
    if not question.strip():
        return "Please enter a question.", []

    chunks = retrieve(question, source_filter=source_filter)
    if not chunks:
        return "No relevant content found in the indexed documents.", []

    context = build_context(chunks)
    prompt = QA_PROMPT.format(context=context, question=question)

    try:
        answer = invoke_llm(prompt)
    except ConnectionError as e:
        return str(e), []

    # Deduplicate sources
    seen = set()
    sources = []
    for c in chunks:
        key = (c["source"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"source": c["source"], "page": c["page"], "score": c["score"]})

    return answer.strip(), sources
