from typing import List, Dict, Optional
from src.vector_store import get_vectorstore
from config.settings import TOP_K
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def retrieve(query: str, k: int = TOP_K, source_filter: Optional[str] = None) -> List[Dict]:
    """Return top-k relevant chunks for a query, optionally filtered by source document."""
    vs = get_vectorstore()
    search_kwargs = {"k": k}
    if source_filter:
        search_kwargs["filter"] = {"source": source_filter}

    try:
        results = vs.similarity_search_with_relevance_scores(query, **search_kwargs)
        chunks = []
        for doc, score in results:
            chunks.append({
                "text": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", 0),
                "chunk_id": doc.metadata.get("chunk_id", ""),
                "score": round(score, 4),
            })
        return chunks
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return []
