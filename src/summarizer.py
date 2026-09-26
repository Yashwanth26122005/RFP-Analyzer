from typing import Optional
from src.retriever import retrieve
from src.rag_pipeline import build_context
from src.llm import invoke_llm
from src.prompts import SUMMARY_PROMPT
from utils.logging_utils import get_logger

logger = get_logger(__name__)

SUMMARY_TOPICS = [
    "project objective overview deliverables",
    "business requirements functional requirements",
    "technical requirements infrastructure",
    "security requirements compliance standards",
    "timeline milestones evaluation criteria budget",
    "risks constraints assumptions",
]

def generate_summary(source_filter: Optional[str] = None) -> str:
    all_chunks = []
    seen_ids = set()
    for topic in SUMMARY_TOPICS:
        chunks = retrieve(topic, k=4, source_filter=source_filter)
        for c in chunks:
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)

    if not all_chunks:
        return "No document content found. Please upload and process an RFP first."

    context = build_context(all_chunks)
    prompt = SUMMARY_PROMPT.format(context=context)
    try:
        return invoke_llm(prompt).strip()
    except ConnectionError as e:
        return str(e)
