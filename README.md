# GenAI-Powered RFP Analyzer — Complete Guide

## What is this project?

An RFP (Request for Proposal) is a document a company sends out when they want to hire someone to build software or provide a service. It contains requirements, timelines, budgets, and rules.

This project uses **Artificial Intelligence** to automatically read, understand, and analyze those RFP PDF documents — so instead of a human spending hours reading them, the AI does it in seconds.

---

## How does it work? (Simple Explanation)

```
You upload a PDF
       ↓
The app reads every page of the PDF
       ↓
The text is split into small pieces called "chunks"
       ↓
Each chunk is converted into numbers (called "embeddings") that represent its meaning
       ↓
These numbers are stored in a database (ChromaDB)
       ↓
When you ask a question, your question is also converted to numbers
       ↓
The app finds the chunks whose numbers are closest to your question's numbers
       ↓
Those chunks are sent to an AI model (llama3.2 via Ollama)
       ↓
The AI reads those chunks and writes an answer
       ↓
You see the answer on screen
```

This technique is called **RAG — Retrieval Augmented Generation**.

---

## Full Project Structure

```
RFP-Analyzer/
├── backend/                  ← API server (FastAPI) — handles all logic
│   ├── __init__.py
│   └── main.py
├── frontend/                 ← User interface (Streamlit) — what you see
│   └── app.py
├── src/                      ← Core AI and analysis logic
│   ├── __init__.py
│   ├── pdf_processor.py      ← Reads PDF files
│   ├── document_chunker.py   ← Splits text into chunks
│   ← embeddings.py          ← Converts text to numbers
│   ├── vector_store.py       ← Stores and searches chunks
│   ├── retriever.py          ← Finds relevant chunks
│   ├── rag_pipeline.py       ← Combines retrieval + AI answer
│   ├── llm.py                ← Connects to Ollama AI model
│   ├── prompts.py            ← Instructions given to the AI
│   ├── summarizer.py         ← Generates executive summary
│   ├── requirement_extractor.py ← Extracts requirements
│   ├── compliance_analyzer.py   ← Finds compliance/security issues
│   ├── risk_analyzer.py         ← Identifies risks
│   ├── clarification.py         ← Generates questions for client
│   ├── comparison.py            ← Compares two RFPs
│   └── exporter.py              ← Exports to Excel/PDF
├── config/
│   └── settings.py           ← All app settings from .env file
├── utils/
│   ├── file_utils.py         ← File saving and hashing helpers
│   ├── logging_utils.py      ← Logging/printing messages
│   └── text_utils.py         ← Text cleaning helpers
├── tests/                    ← Automated tests
├── data/
│   ├── uploads/              ← Uploaded PDFs are saved here
│   └── processed/            ← Processed files go here
├── vectorstore/              ← ChromaDB database files stored here
├── .env                      ← Your secret settings (not on GitHub)
├── .env.example              ← Example of what .env should look like
├── requirements.txt          ← List of all Python libraries needed
└── README.md                 ← This file
```

---

## Technology Stack Explained

| Technology | What it is | Why we use it |
|---|---|---|
| **Python** | Programming language | Everything is written in Python |
| **Streamlit** | Python web UI library | Builds the visual interface without HTML/CSS |
| **FastAPI** | Python web framework | Creates the backend API server |
| **Ollama** | Tool to run AI models locally | Runs llama3.2 on your own computer |
| **llama3.2** | AI language model (LLM) | The brain that reads and answers questions |
| **ChromaDB** | Vector database | Stores text chunks as numbers for fast search |
| **LangChain** | AI framework | Connects all AI components together |
| **sentence-transformers** | Embedding model | Converts text to numbers (vectors) |
| **pypdf** | PDF reader library | Extracts text from PDF files |
| **pandas** | Data table library | Displays data in tables |
| **reportlab** | PDF generator | Creates PDF export reports |
| **openpyxl** | Excel library | Creates Excel export files |

---

## Complete Workflow (Step by Step)

### Step 1 — You Upload a PDF
You go to the "Upload RFP" page and select a PDF file.

### Step 2 — PDF is Read
`pdf_processor.py` opens the PDF and reads text from every page.

### Step 3 — Text is Cleaned
`text_utils.py` removes weird characters and extra spaces from the text.

### Step 4 — Text is Split into Chunks
`document_chunker.py` splits the long text into small overlapping pieces (1000 characters each with 200 character overlap).

### Step 5 — Chunks are Converted to Numbers
`embeddings.py` uses the `all-MiniLM-L6-v2` model to convert each chunk into a list of 384 numbers that represent its meaning.

### Step 6 — Numbers are Stored
`vector_store.py` saves all those numbers into ChromaDB database on your computer.

### Step 7 — You Ask a Question or Click Analyze
You type a question or click a button like "Extract Requirements".

### Step 8 — Relevant Chunks are Found
`retriever.py` converts your question to numbers and finds the 5 most similar chunks in ChromaDB.

### Step 9 — AI Generates Answer
`rag_pipeline.py` sends those chunks + your question to llama3.2 via Ollama. The AI reads them and writes an answer.

### Step 10 — Answer is Shown
The frontend displays the answer, table, or analysis on your screen.

---

## Every File Explained in Detail

---

### `config/settings.py` — App Settings

```python
import os
from dotenv import load_dotenv
```
- `os` — built-in Python module to read environment variables (settings stored outside code)
- `dotenv` — reads the `.env` file and loads its values into the program

```python
load_dotenv()
```
- Reads your `.env` file so all settings become available

```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
```
- Reads `LLM_PROVIDER` from `.env`. If not found, uses `"ollama"` as default
- This tells the app which AI provider to use

```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
```
- Which AI model to use (`llama3.2`)
- Where Ollama is running (on your computer at port 11434)

```python
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
```
- Each text chunk will be 1000 characters long
- Chunks overlap by 200 characters so no information is lost at boundaries

```python
TOP_K = int(os.getenv("TOP_K", "5"))
```
- When searching, return the top 5 most relevant chunks

```python
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vectorstore")
```
- Where to save the ChromaDB database files on your computer

---

### `utils/logging_utils.py` — Logging Helper

```python
import logging
import sys
```
- `logging` — Python's built-in system for printing messages with timestamps and levels
- `sys` — gives access to standard output (the terminal/console)

```python
def get_logger(name: str) -> logging.Logger:
```
- A function that creates a logger. `name` is usually the file name (e.g. `src.llm`)

```python
    logger = logging.getLogger(name)
```
- Gets or creates a logger with that name

```python
    if not logger.handlers:
```
- Only add a handler if one doesn't already exist (prevents duplicate messages)

```python
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
```
- Prints logs to the terminal in format: `2024-01-01 12:00:00 [INFO] src.llm: message`

```python
        logger.setLevel(logging.INFO)
```
- Only show INFO level and above (not DEBUG which is too detailed)

---

### `utils/text_utils.py` — Text Cleaning

```python
import re
```
- `re` — Python's regular expressions module for pattern matching in text

```python
def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
```
- Replaces multiple spaces/newlines/tabs with a single space
- `\s+` means "one or more whitespace characters"

```python
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
```
- Removes non-ASCII characters (weird symbols from PDFs)
- `[^\x00-\x7F]` means "any character NOT in the standard ASCII range"

```python
def is_meaningful(text: str, min_chars: int = 50) -> bool:
    return len(text.strip()) >= min_chars
```
- Returns True if text has at least 50 characters (not a blank or near-blank page)

---

### `utils/file_utils.py` — File Helpers

```python
import os
import hashlib
```
- `os` — for file/folder operations
- `hashlib` — for generating a unique fingerprint (hash) of a file

```python
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
```
- Creates a folder if it doesn't exist. `exist_ok=True` means don't crash if it already exists

```python
def file_hash(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
```
- Reads the file in 8192-byte pieces and generates an MD5 hash
- This hash is a unique fingerprint — if the file changes, the hash changes
- Used to detect if a file was already processed (avoid re-processing)

```python
def save_uploaded_file(uploaded_file, directory: str) -> str:
    dest = os.path.join(directory, uploaded_file.name)
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest
```
- Saves the uploaded file from Streamlit to the uploads folder
- `"wb"` means write in binary mode (needed for PDFs)
- Returns the full path where the file was saved

---

### `src/pdf_processor.py` — PDF Reader

```python
from pypdf import PdfReader
```
- `PdfReader` — the class that opens and reads PDF files

```python
def extract_pdf_pages(filepath: str) -> List[Dict]:
```
- Takes a file path, returns a list of dictionaries (one per page)

```python
    reader = PdfReader(filepath)
```
- Opens the PDF file

```python
    source = filepath.split("/")[-1].split("\\")[-1]
```
- Extracts just the filename from the full path (works on both Windows and Mac/Linux)

```python
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = clean_text(text)
```
- Loops through every page, extracts its text, cleans it

```python
        pages.append({
            "text": text,
            "source": source,
            "page": i + 1,
            "total_pages": len(reader.pages),
        })
```
- Stores each page as a dictionary with its text, filename, page number, and total pages

---

### `src/document_chunker.py` — Text Splitter

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```
- LangChain's smart text splitter that tries to split at natural boundaries (paragraphs, sentences)

```python
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,        # max 1000 characters per chunk
        chunk_overlap=chunk_overlap,  # 200 characters shared between chunks
        separators=["\n\n", "\n", ". ", " ", ""],
    )
```
- Tries to split at double newlines first, then single newlines, then sentences, then words
- Overlap ensures context isn't lost at chunk boundaries

```python
        chunk_id = f"{source}_{page_num}_{chunk_counters[key]:02d}"
```
- Creates a unique ID for each chunk like `document.pdf_3_01`
- Used to avoid storing the same chunk twice

---

### `src/embeddings.py` — Text to Numbers

```python
from langchain_huggingface import HuggingFaceEmbeddings
```
- Loads embedding models from HuggingFace (a platform for AI models)

```python
_embedding_instance = None

def get_embeddings():
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(...)
    return _embedding_instance
```
- Uses a singleton pattern — loads the model only once and reuses it
- Loading the model takes time, so we don't want to reload it every time

```python
        model_name=EMBEDDING_MODEL,          # "sentence-transformers/all-MiniLM-L6-v2"
        model_kwargs={"device": "cpu"},       # run on CPU (not GPU)
        encode_kwargs={"normalize_embeddings": True},  # normalize vectors to length 1
```
- `all-MiniLM-L6-v2` converts text into 384 numbers
- Normalization makes similarity comparisons more accurate

---

### `src/vector_store.py` — Database

```python
from langchain_chroma import Chroma
```
- LangChain's wrapper around ChromaDB

```python
def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=VECTOR_DB_PATH,
        )
    return _vectorstore
```
- Opens (or creates) the ChromaDB database
- `persist_directory` means data is saved to disk, not lost when app restarts

```python
def add_chunks(chunks: List[Dict]):
    ...
    existing_ids = set(result.get("ids", []))
    ...
    if cid in existing_ids:
        continue
```
- Before adding chunks, checks which ones already exist
- Skips duplicates so the same document isn't indexed twice

```python
    vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
```
- Adds text chunks to ChromaDB. ChromaDB automatically converts them to vectors using the embedding model

---

### `src/retriever.py` — Search Engine

```python
def retrieve(query: str, k: int = TOP_K, source_filter: Optional[str] = None):
```
- `query` — the question or topic to search for
- `k` — how many results to return (default 5)
- `source_filter` — optionally limit search to one specific document

```python
    search_kwargs = {"k": k}
    if source_filter:
        search_kwargs["filter"] = {"source": source_filter}
```
- Builds search parameters. If a document filter is set, only search within that document

```python
    results = vs.similarity_search_with_relevance_scores(query, **search_kwargs)
```
- Converts the query to a vector and finds the k most similar vectors in the database
- Returns each result with a relevance score (0 to 1, higher = more relevant)

---

### `src/llm.py` — AI Model Connection

```python
from langchain_ollama import OllamaLLM
```
- LangChain's connector to Ollama

```python
def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    return _llm_instance
```
- Creates a connection to Ollama running on your computer
- Singleton pattern — only one connection is created

```python
def invoke_llm(prompt: str) -> str:
    try:
        llm = get_llm()
        return llm.invoke(prompt)
    except Exception as e:
        raise ConnectionError(f"LLM unavailable. Ensure Ollama is running...")
```
- Sends a prompt (text instruction) to the AI model and returns its response
- If Ollama isn't running, raises a clear error message

---

### `src/prompts.py` — AI Instructions

These are the instructions (called prompts) sent to the AI model. They tell the AI exactly what to do.

```python
QA_PROMPT = """You are an expert RFP analysis assistant. Answer the user's question using ONLY the information provided...
{context}
Question: {question}
Answer:"""
```
- `{context}` is replaced with the retrieved chunks
- `{question}` is replaced with the user's question
- The rules prevent the AI from making up information

Each prompt is designed for a specific task:
- `QA_PROMPT` — for answering questions
- `SUMMARY_PROMPT` — for generating executive summaries
- `REQUIREMENTS_PROMPT` — for extracting requirements into a table
- `SECURITY_PROMPT` — for finding security requirements
- `COMPLIANCE_PROMPT` — for finding compliance standards
- `RISK_PROMPT` — for identifying risks with severity levels
- `CLARIFICATION_PROMPT` — for generating client questions
- `COMPARISON_PROMPT` — for comparing two RFPs side by side

---

### `src/rag_pipeline.py` — The Core Pipeline

```python
def build_context(chunks: List[Dict]) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c['source']}, Page {c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)
```
- Formats retrieved chunks into readable context text
- Adds source and page number labels so the AI knows where each piece came from

```python
def answer_question(question: str, source_filter=None):
    chunks = retrieve(question, source_filter=source_filter)
    context = build_context(chunks)
    prompt = QA_PROMPT.format(context=context, question=question)
    answer = invoke_llm(prompt)
    ...
    return answer.strip(), sources
```
- Full RAG pipeline: retrieve → build context → format prompt → call AI → return answer
- Also returns deduplicated source references

---

### `src/summarizer.py` — Summary Generator

```python
SUMMARY_TOPICS = [
    "project objective overview deliverables",
    "business requirements functional requirements",
    "technical requirements infrastructure",
    ...
]
```
- Multiple search queries to cover all aspects of the RFP
- Using multiple queries ensures comprehensive coverage

```python
def generate_summary(source_filter=None):
    all_chunks = []
    seen_ids = set()
    for topic in SUMMARY_TOPICS:
        chunks = retrieve(topic, k=4, source_filter=source_filter)
        for c in chunks:
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)
```
- Retrieves chunks for each topic, deduplicates them using `seen_ids`
- Then sends all unique chunks to the AI with the summary prompt

---

### `src/requirement_extractor.py` — Requirements Extractor

```python
def _parse_pipe_table(raw: str, keys: List[str]) -> List[Dict]:
    for line in raw.splitlines():
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= len(keys):
            rows.append(dict(zip(keys, parts[:len(keys)])))
```
- The AI returns requirements in pipe-separated format: `Technical | Use HTTPS | Page 5`
- This function parses that text into a list of dictionaries
- `zip(keys, parts)` pairs column names with values

---

### `src/risk_analyzer.py` — Risk Analyzer

```python
RISK_TOPICS = [
    "timeline deadline milestones schedule",
    "technical complexity integration dependencies",
    "security requirements ambiguity",
    ...
]
```
- Searches for content related to common risk areas

```python
def _parse_risks(raw: str) -> List[Dict]:
    keys = ["category", "description", "severity", "evidence", "clarification"]
    ...
    for k in keys:
        row.setdefault(k, "N/A")
```
- Parses the AI's pipe-separated risk output
- `setdefault` fills in "N/A" for any missing fields

---

### `src/compliance_analyzer.py` — Compliance & Security

```python
def analyze_compliance(source_filter=None):
    return _run_analysis(COMPLIANCE_TOPICS, COMPLIANCE_PROMPT, ["standard", "requirement", "page"], source_filter)

def analyze_security(source_filter=None):
    return _run_analysis(SECURITY_TOPICS, SECURITY_PROMPT, ["category", "requirement", "page"], source_filter)
```
- Both functions use the same `_run_analysis` helper but with different topics, prompts, and column names

---

### `src/comparison.py` — RFP Comparison

```python
def compare_rfps(source_a: str, source_b: str):
    for topic in COMPARISON_TOPICS:
        for c in retrieve(topic, k=4, source_filter=source_a):
            ...
        for c in retrieve(topic, k=4, source_filter=source_b):
            ...
    prompt = COMPARISON_PROMPT.format(context_a=context_a, context_b=context_b)
```
- Retrieves relevant chunks from BOTH documents separately
- Sends both contexts to the AI which compares them side by side

---

### `src/exporter.py` — Export to Excel/PDF

```python
def export_excel(data: Dict[str, List[Dict]]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet_name, rows in data.items():
            if rows:
                df = pd.DataFrame(rows)
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buf.getvalue()
```
- Creates an Excel file in memory (not on disk) using `BytesIO`
- Each analysis section (Requirements, Risks, etc.) becomes a separate sheet
- Returns the file as bytes so Streamlit can offer it as a download

---

### `backend/main.py` — FastAPI API Server

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
app = FastAPI(title="RFP Analyzer API")
```
- Creates the API server. FastAPI automatically generates API documentation at `http://localhost:8000/docs`

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
- CORS (Cross-Origin Resource Sharing) allows the frontend (port 8501) to call the backend (port 8000)

```python
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
```
- `@app.post("/upload")` — defines a POST endpoint at `/upload`
- `UploadFile` — FastAPI automatically handles the uploaded file

```python
@app.post("/chat")
def chat(req: QuestionRequest):
    answer, sources = answer_question(req.question, source_filter=req.source_filter)
    return {"answer": answer, "sources": sources}
```
- Receives a JSON request with a question, calls the RAG pipeline, returns the answer

---

### `frontend/app.py` — Streamlit UI

```python
API_URL = "http://localhost:8000"
```
- All requests go to the FastAPI backend

```python
def api(method, endpoint, **kwargs):
    resp = getattr(requests, method)(f"{API_URL}{endpoint}", **kwargs)
    resp.raise_for_status()
    return resp.json()
```
- A helper function to call any API endpoint
- `getattr(requests, method)` dynamically calls `requests.get`, `requests.post`, etc.
- `raise_for_status()` raises an error if the server returns an error code

```python
st.set_page_config(page_title="GenAI-Powered RFP Analyzer", layout="wide")
```
- Configures the Streamlit page title and layout

```python
page = st.radio("Navigation", ["🏠 Dashboard", "📤 Upload RFP", ...])
```
- Creates the sidebar navigation menu. The selected value is stored in `page`

```python
if page == "📤 Upload RFP":
    uploaded_files = st.file_uploader(...)
    if st.button(f"Process {uf.name}"):
        result = api("post", "/upload", files={"file": (uf.name, uf.getvalue(), "application/pdf")})
```
- When user clicks the Process button, sends the PDF to the backend `/upload` endpoint

---

## Installation & Running

### 1. Install Python 3.11
Download from [python.org](https://python.org) — check "Add to PATH" during install.

### 2. Install Ollama
Download from [ollama.com](https://ollama.com) and install.

### 3. Clone the project
```bash
git clone https://github.com/Yashwanth26122005/RFP-Analyzer.git
cd RFP-Analyzer
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Set up environment
```bash
copy .env.example .env
```

### 6. Pull the AI model
```bash
ollama pull llama3.2
```

### 7. Run the backend (Terminal 1)
```bash
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```

### 8. Run the frontend (Terminal 2)
```bash
py -3.11 -m streamlit run frontend/app.py
```

### 9. Open browser
Go to **http://localhost:8501**

---

## API Endpoints (Backend)

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/upload` | Upload and process a PDF |
| GET | `/stats` | Get database statistics |
| POST | `/chat` | Ask a question about the RFP |
| POST | `/summary` | Generate executive summary |
| POST | `/requirements` | Extract requirements |
| POST | `/security` | Run security analysis |
| POST | `/compliance` | Run compliance analysis |
| POST | `/risks` | Run risk analysis |
| POST | `/clarifications` | Generate clarification questions |
| POST | `/compare` | Compare two RFPs |
| POST | `/export/excel` | Export data to Excel |

Full interactive API docs available at: **http://localhost:8000/docs**

---

## Common Issues

**"Cannot connect to backend"**
→ Make sure you ran `uvicorn backend.main:app --port 8000` in a terminal

**"LLM unavailable"**
→ Make sure Ollama is running. Open a terminal and run `ollama serve`

**"No relevant content found"**
→ Make sure you uploaded and processed a PDF first

**PDF pages show no text**
→ The PDF might be scanned (image-based). This app only works with text-based PDFs

---

## How RAG Works (Visual)

```
Your Question: "What are the security requirements?"
       ↓
Convert to vector: [0.23, -0.45, 0.12, ... 384 numbers]
       ↓
Search ChromaDB for similar vectors
       ↓
Found chunks:
  - "All data must be encrypted using AES-256..." (score: 0.92)
  - "Authentication must use MFA..." (score: 0.89)
  - "Annual penetration testing required..." (score: 0.85)
       ↓
Build prompt:
  "Context: [those 3 chunks]
   Question: What are the security requirements?
   Answer:"
       ↓
Send to llama3.2
       ↓
AI Answer: "The RFP requires AES-256 encryption, MFA authentication,
            and annual penetration testing..."
```
