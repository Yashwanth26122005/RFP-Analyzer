from typing import List, Dict
from src.retriever import retrieve
from src.rag_pipeline import build_context
from src.llm import invoke_llm
from src.prompts import COMPARISON_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

COMPARISON_TOPICS = [
    "business requirements objectives",
    "technical requirements architecture",
    "security compliance requirements",
    "timeline deliverables milestones",
    "evaluation criteria scoring",
]

def compare_rfps(source_a: str, source_b: str) -> List[Dict]:
    chunks_a, chunks_b = [], []
    seen_a, seen_b = set(), set()

    for topic in COMPARISON_TOPICS:
        for c in retrieve(topic, k=4, source_filter=source_a):
            if c["chunk_id"] not in seen_a:
                seen_a.add(c["chunk_id"])
                chunks_a.append(c)
        for c in retrieve(topic, k=4, source_filter=source_b):
            if c["chunk_id"] not in seen_b:
                seen_b.add(c["chunk_id"])
                chunks_b.append(c)

    if not chunks_a or not chunks_b:
        return []

    context_a = build_context(chunks_a)
    context_b = build_context(chunks_b)
    prompt = COMPARISON_PROMPT.format(context_a=context_a, context_b=context_b)

    try:
        raw = invoke_llm(prompt).strip()
    except ConnectionError as e:
        logger.error(e)
        return []

    return _parse_comparison(raw)

def _parse_comparison(raw: str) -> List[Dict]:
    rows = []
    keys = ["category", "aspect", "rfp_a", "rfp_b"]
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or set(line) <= set("|-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 3:
            row = dict(zip(keys, parts[:len(keys)]))
            for k in keys:
                row.setdefault(k, "N/A")
            rows.append(row)
    return rows
