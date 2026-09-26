from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def chunk_pages(pages: List[Dict], chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """Split page texts into overlapping chunks, preserving metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    chunk_counters: Dict[str, int] = {}

    for page in pages:
        text = page["text"]
        if not text.strip():
            continue
        splits = splitter.split_text(text)
        for split in splits:
            source = page["source"]
            page_num = page["page"]
            key = f"{source}_{page_num}"
            chunk_counters[key] = chunk_counters.get(key, 0) + 1
            chunk_id = f"{source}_{page_num}_{chunk_counters[key]:02d}"
            chunks.append({
                "text": split,
                "source": source,
                "page": page_num,
                "chunk_id": chunk_id,
            })

    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages.")
    return chunks
