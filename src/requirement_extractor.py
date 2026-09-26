from typing import List, Dict, Optional
from src.retriever import retrieve
from src.rag_pipeline import build_context
from src.llm import invoke_llm
from src.prompts import REQUIREMENTS_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

REQUIREMENT_TOPICS = [
    "business requirements objectives goals",
    "functional requirements features capabilities",
    "technical requirements architecture infrastructure",
    "security requirements encryption authentication",
    "compliance regulatory standards certifications",
    "data requirements storage processing",
    "integration API interfaces",
    "support SLA maintenance",
    "performance scalability availability",
]

def extract_requirements(source_filter: Optional[str] = None) -> List[Dict]:
    all_chunks = []
    seen_ids = set()
    for topic in REQUIREMENT_TOPICS:
        for c in retrieve(topic, k=4, source_filter=source_filter):
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)

    if not all_chunks:
        return []

    context = build_context(all_chunks)
    prompt = REQUIREMENTS_PROMPT.format(context=context)
    try:
        raw = invoke_llm(prompt).strip()
    except ConnectionError as e:
        logger.error(e)
        return []

    return _parse_pipe_table(raw, ["category", "requirement", "page"])

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
