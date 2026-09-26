import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
from unittest.mock import patch, MagicMock
from src.pdf_processor import extract_pdf_pages, get_pdf_metadata


def _make_mock_reader(texts):
    pages = []
    for t in texts:
        p = MagicMock()
        p.extract_text.return_value = t
        pages.append(p)
    reader = MagicMock()
    reader.pages = pages
    return reader


@patch("src.pdf_processor.PdfReader")
def test_extract_pages_returns_correct_count(mock_reader_cls):
    mock_reader_cls.return_value = _make_mock_reader(["Page one text content here.", "Page two text content here."])
    pages = extract_pdf_pages("dummy.pdf")
    assert len(pages) == 2


@patch("src.pdf_processor.PdfReader")
def test_extract_pages_metadata(mock_reader_cls):
    mock_reader_cls.return_value = _make_mock_reader(["Some meaningful text on this page for testing purposes."])
    pages = extract_pdf_pages("my_rfp.pdf")
    assert pages[0]["source"] == "my_rfp.pdf"
    assert pages[0]["page"] == 1


@patch("src.pdf_processor.PdfReader")
def test_empty_page_handled(mock_reader_cls):
    mock_reader_cls.return_value = _make_mock_reader(["", "Real content on page two here."])
    pages = extract_pdf_pages("dummy.pdf")
    assert pages[0]["text"] == ""
    assert len(pages) == 2


@patch("src.pdf_processor.PdfReader")
def test_invalid_pdf_raises(mock_reader_cls):
    mock_reader_cls.side_effect = Exception("Not a PDF")
    with pytest.raises(ValueError):
        extract_pdf_pages("bad.pdf")
