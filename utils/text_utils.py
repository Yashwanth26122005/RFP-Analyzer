import re

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def truncate_text(text: str, max_chars: int = 500) -> str:
    return text[:max_chars] + "..." if len(text) > max_chars else text

def is_meaningful(text: str, min_chars: int = 50) -> bool:
    return len(text.strip()) >= min_chars
