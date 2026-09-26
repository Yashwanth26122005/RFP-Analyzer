from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import EMBEDDING_MODEL
from utils.logging_utils import get_logger

logger = get_logger(__name__)
_embedding_instance = None

def get_embeddings() -> HuggingFaceEmbeddings:
    global _embedding_instance
    if _embedding_instance is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_instance
