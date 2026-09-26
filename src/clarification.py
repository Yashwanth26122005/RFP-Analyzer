from typing import List, Dict, Optional
from src.retriever import retrieve
from src.rag_pipeline import build_context
from src.llm import invoke_llm
from src.prompts import CLARIFICATION_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

CLARIFICATION_TOPICS = [
    "unclear ambiguous requirements",
    "timeline schedule milestones",
    "budget cost pricing commercial",
    "SLA support response time",
    "technical specifications architecture",
    "security compliance requirements",
    "integration dependencies third party",
    "data ownership privacy",
]

def generate_clarifications(source_filter: Optional[str] = None) -> List[Dict]:
    all_chunks = []
    seen_ids = set()
    for topic in CLARIFICATION_TOPICS:
        for c in retrieve(topic, k=3, source_filter=source_filter):
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)

    if not all_chunks:
        return []

    context = build_context(all_chunks)
    prompt = CLARIFICATION_PROMPT.format(context=context)
    try:
        raw = invoke_llm(prompt).strip()
    except ConnectionError as e:
        logger.error(e)
        return []

    return _parse_pipe_table(raw, ["group", "question"])

def _parse_pipe_table(raw: str, keys: List[str]) -> List[Dict]:
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or set(line) <= set("|-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= len(keys):
            rows.append(dict(zip(keys, parts[:len(keys)])))
    return rows
