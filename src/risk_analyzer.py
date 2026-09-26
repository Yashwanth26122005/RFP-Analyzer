from typing import List, Dict, Optional
from src.retriever import retrieve
from src.rag_pipeline import build_context
from src.llm import invoke_llm
from src.prompts import RISK_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

RISK_TOPICS = [
    "timeline deadline milestones schedule",
    "technical complexity integration dependencies",
    "security requirements ambiguity",
    "compliance regulatory requirements",
    "budget cost pricing",
    "SLA support requirements unclear",
    "resource staffing team requirements",
    "data migration legacy systems",
]

def analyze_risks(source_filter: Optional[str] = None) -> List[Dict]:
    all_chunks = []
    seen_ids = set()
    for topic in RISK_TOPICS:
        for c in retrieve(topic, k=3, source_filter=source_filter):
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)

    if not all_chunks:
        return []

    context = build_context(all_chunks)
    prompt = RISK_PROMPT.format(context=context)
    try:
        raw = invoke_llm(prompt).strip()
    except ConnectionError as e:
        logger.error(e)
        return []

    return _parse_risks(raw)

def _parse_risks(raw: str) -> List[Dict]:
    rows = []
    keys = ["category", "description", "severity", "evidence", "clarification"]
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or set(line) <= set("|-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 3:
            row = dict(zip(keys, parts[:len(keys)]))
            # Pad missing fields
            for k in keys:
                row.setdefault(k, "N/A")
            rows.append(row)
    return rows
