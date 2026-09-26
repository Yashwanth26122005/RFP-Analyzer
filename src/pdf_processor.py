from pypdf import PdfReader
from typing import List, Dict
from utils.text_utils import clean_text, is_meaningful
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def extract_pdf_pages(filepath: str) -> List[Dict]:
    """Extract text from each page of a PDF, returning list of page dicts."""
    pages = []
    try:
        reader = PdfReader(filepath)
        source = filepath.split("/")[-1].split("\\")[-1]
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                text = clean_text(text)
                if not is_meaningful(text):
                    logger.warning(f"Page {i+1} of '{source}' has little/no extractable text.")
                pages.append({
                    "text": text,
                    "source": source,
                    "page": i + 1,
                    "total_pages": len(reader.pages),
                })
            except Exception as e:
                logger.error(f"Error extracting page {i+1}: {e}")
                pages.append({"text": "", "source": source, "page": i + 1, "total_pages": len(reader.pages)})
    except Exception as e:
        logger.error(f"Failed to read PDF '{filepath}': {e}")
        raise ValueError(f"Could not read PDF: {e}")
    return pages

def get_pdf_metadata(filepath: str) -> Dict:
    try:
        reader = PdfReader(filepath)
        source = filepath.split("/")[-1].split("\\")[-1]
        return {
            "source": source,
            "total_pages": len(reader.pages),
            "filepath": filepath,
        }
    except Exception as e:
        raise ValueError(f"Could not read PDF metadata: {e}")
