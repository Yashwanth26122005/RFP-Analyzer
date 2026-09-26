from typing import List, Dict, Optional
from src.retriever import retrieve
from src.rag_pipeline import build_context
from src.llm import invoke_llm
from src.prompts import COMPLIANCE_PROMPT, SECURITY_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

COMPLIANCE_TOPICS = [
    "ISO certification compliance standard",
    "SOC audit report",
    "GDPR data protection privacy regulation",
    "HIPAA healthcare data",
    "PCI DSS payment card",
    "data residency sovereignty",
    "regulatory compliance certification audit",
]

SECURITY_TOPICS = [
    "encryption data security",
    "authentication authorization access control",
    "network security firewall",
    "vulnerability penetration testing",
    "incident response security monitoring",
    "backup disaster recovery",
    "data privacy protection",
]

def analyze_compliance(source_filter: Optional[str] = None) -> List[Dict]:
    return _run_analysis(COMPLIANCE_TOPICS, COMPLIANCE_PROMPT, ["standard", "requirement", "page"], source_filter)

def analyze_security(source_filter: Optional[str] = None) -> List[Dict]:
    return _run_analysis(SECURITY_TOPICS, SECURITY_PROMPT, ["category", "requirement", "page"], source_filter)

def _run_analysis(topics, prompt_template, keys, source_filter):
    all_chunks = []
    seen_ids = set()
    for topic in topics:
        for c in retrieve(topic, k=3, source_filter=source_filter):
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)

    if not all_chunks:
        return []

    context = build_context(all_chunks)
    prompt = prompt_template.format(context=context)
    try:
        raw = invoke_llm(prompt).strip()
    except ConnectionError as e:
        logger.error(e)
        return []

    return _parse_pipe_table(raw, keys)

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
