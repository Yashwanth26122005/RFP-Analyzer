import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil
import tempfile

from config.settings import UPLOAD_DIRECTORY, PROCESSED_DIRECTORY
from utils.file_utils import save_uploaded_file, file_hash, ensure_dir
from utils.logging_utils import get_logger

logger = get_logger(__name__)

app = FastAPI(title="RFP Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_dir(UPLOAD_DIRECTORY)
ensure_dir(PROCESSED_DIRECTORY)


# ── Models ──────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    source_filter: Optional[str] = None

class SourceRequest(BaseModel):
    source_filter: Optional[str] = None

class CompareRequest(BaseModel):
    source_a: str
    source_b: str


# ── Upload & Process ─────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    from src.pdf_processor import extract_pdf_pages, get_pdf_metadata
    from src.document_chunker import chunk_pages
    from src.vector_store import add_chunks

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    tmp_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        pages = extract_pdf_pages(tmp_path)
        meta = get_pdf_metadata(tmp_path)
        chunks = chunk_pages(pages)
        add_chunks(chunks)
        return {
            "filename": file.filename,
            "pages": meta["total_pages"],
            "chunks": len(chunks),
            "hash": file_hash(tmp_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    from src.vector_store import get_collection_stats
    return get_collection_stats()


# ── Chat / Q&A ───────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(req: QuestionRequest):
    from src.rag_pipeline import answer_question
    answer, sources = answer_question(req.question, source_filter=req.source_filter)
    return {"answer": answer, "sources": sources}


# ── Executive Summary ────────────────────────────────────────────────────────

@app.post("/summary")
def summary(req: SourceRequest):
    from src.summarizer import generate_summary
    return {"summary": generate_summary(source_filter=req.source_filter)}


# ── Requirements ─────────────────────────────────────────────────────────────

@app.post("/requirements")
def requirements(req: SourceRequest):
    from src.requirement_extractor import extract_requirements
    return {"requirements": extract_requirements(source_filter=req.source_filter)}


# ── Security Analysis ────────────────────────────────────────────────────────

@app.post("/security")
def security(req: SourceRequest):
    from src.compliance_analyzer import analyze_security
    return {"findings": analyze_security(source_filter=req.source_filter)}


# ── Compliance Analysis ──────────────────────────────────────────────────────

@app.post("/compliance")
def compliance(req: SourceRequest):
    from src.compliance_analyzer import analyze_compliance
    return {"findings": analyze_compliance(source_filter=req.source_filter)}


# ── Risk Analysis ────────────────────────────────────────────────────────────

@app.post("/risks")
def risks(req: SourceRequest):
    from src.risk_analyzer import analyze_risks
    return {"risks": analyze_risks(source_filter=req.source_filter)}


# ── Clarification Questions ──────────────────────────────────────────────────

@app.post("/clarifications")
def clarifications(req: SourceRequest):
    from src.clarification import generate_clarifications
    return {"questions": generate_clarifications(source_filter=req.source_filter)}


# ── RFP Comparison ───────────────────────────────────────────────────────────

@app.post("/compare")
def compare(req: CompareRequest):
    from src.comparison import compare_rfps
    return {"comparison": compare_rfps(req.source_a, req.source_b)}


# ── Export ───────────────────────────────────────────────────────────────────

@app.post("/export/excel")
def export_excel(data: dict):
    from src.exporter import export_excel as _export_excel
    from fastapi.responses import Response
    xlsx = _export_excel(data)
    return Response(content=xlsx, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename=rfp_analysis.xlsx"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
