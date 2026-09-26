from langchain_ollama import OllamaLLM
from config.settings import LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_BASE_URL
from utils.logging_utils import get_logger

logger = get_logger(__name__)
_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        if LLM_PROVIDER == "ollama":
            logger.info(f"Connecting to Ollama model: {OLLAMA_MODEL}")
            _llm_instance = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
    return _llm_instance

def invoke_llm(prompt: str) -> str:
    try:
        llm = get_llm()
        return llm.invoke(prompt)
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        raise ConnectionError(f"LLM unavailable. Ensure Ollama is running with model '{OLLAMA_MODEL}'. Error: {e}")

def reset_llm():
    global _llm_instance
    _llm_instance = None
