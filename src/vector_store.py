from typing import List, Dict, Set
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from src.embeddings import get_embeddings
from config.settings import VECTOR_DB_PATH, CHROMA_COLLECTION_NAME
from utils.logging_utils import get_logger

logger = get_logger(__name__)
_vectorstore = None

def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=VECTOR_DB_PATH,
        )
    return _vectorstore

def get_indexed_sources() -> Set[str]:
    vs = get_vectorstore()
    try:
        result = vs.get(include=["metadatas"])
        return {m.get("source", "") for m in result["metadatas"] if m}
    except Exception:
        return set()

def add_chunks(chunks: List[Dict]):
    vs = get_vectorstore()
    existing_ids = set()
    try:
        result = vs.get(include=[])
        existing_ids = set(result.get("ids", []))
    except Exception:
        pass

    texts, metadatas, ids = [], [], []
    for chunk in chunks:
        cid = chunk["chunk_id"]
        if cid in existing_ids:
            continue
        texts.append(chunk["text"])
        metadatas.append({"source": chunk["source"], "page": chunk["page"], "chunk_id": cid})
        ids.append(cid)

    if texts:
        vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        logger.info(f"Added {len(texts)} new chunks to vector store.")
    else:
        logger.info("No new chunks to add (all already indexed).")

def get_collection_stats() -> Dict:
    vs = get_vectorstore()
    try:
        result = vs.get(include=["metadatas"])
        metadatas = result.get("metadatas", [])
        sources = {m.get("source") for m in metadatas if m}
        return {"total_chunks": len(metadatas), "documents": list(sources)}
    except Exception:
        return {"total_chunks": 0, "documents": []}

def reset_vectorstore():
    global _vectorstore
    vs = get_vectorstore()
    vs.delete_collection()
    _vectorstore = None
