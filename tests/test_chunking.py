import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.document_chunker import chunk_pages


SAMPLE_PAGES = [
    {
        "text": "This is a sample RFP requirement. " * 50,
        "source": "test_rfp.pdf",
        "page": 1,
        "total_pages": 2,
    },
    {
        "text": "Security requirements include encryption and access control. " * 30,
        "source": "test_rfp.pdf",
        "page": 2,
        "total_pages": 2,
    },
]


def test_chunks_generated():
    chunks = chunk_pages(SAMPLE_PAGES)
    assert len(chunks) > 0


def test_chunk_metadata_preserved():
    chunks = chunk_pages(SAMPLE_PAGES)
    for c in chunks:
        assert "source" in c
        assert "page" in c
        assert "chunk_id" in c
        assert "text" in c


def test_chunk_ids_unique():
    chunks = chunk_pages(SAMPLE_PAGES)
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))


def test_empty_page_skipped():
    pages = [{"text": "", "source": "test.pdf", "page": 1, "total_pages": 1}]
    chunks = chunk_pages(pages)
    assert len(chunks) == 0


def test_chunk_size_respected():
    chunks = chunk_pages(SAMPLE_PAGES, chunk_size=200, chunk_overlap=20)
    for c in chunks:
        assert len(c["text"]) <= 300  # allow some tolerance
