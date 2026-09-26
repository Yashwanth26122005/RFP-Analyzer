import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from utils.file_utils import save_uploaded_file, file_hash, ensure_dir
from utils.logging_utils import get_logger
from config.settings import UPLOAD_DIRECTORY, PROCESSED_DIRECTORY

logger = get_logger(__name__)

st.set_page_config(
    page_title="GenAI-Powered RFP Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ──────────────────────────────────────────────────
for key, default in {
    "processed_docs": {},   # {filename: {pages, chunks, hash}}
    "chat_history": [],
    "summary": {},
    "requirements": {},
    "security": {},
    "compliance": {},
    "risks": {},
    "clarifications": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

ensure_dir(UPLOAD_DIRECTORY)
ensure_dir(PROCESSED_DIRECTORY)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📄 RFP Analyzer")
    st.caption("GenAI-Powered Document Intelligence")
    st.divider()
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📤 Upload RFP", "💬 Chat / Q&A", "📋 Executive Summary",
         "📌 Requirements", "🔒 Security Analysis", "✅ Compliance Analysis",
         "⚠️ Risk Analysis", "❓ Clarification Questions", "🔀 RFP Comparison", "📥 Export"],
        label_visibility="collapsed",
    )
    st.divider()
    if st.session_state.processed_docs:
        st.markdown("**Indexed Documents**")
        for doc in st.session_state.processed_docs:
            info = st.session_state.processed_docs[doc]
            st.markdown(f"- 📄 `{doc}` ({info['pages']}p)")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("GenAI-Powered RFP Analyzer")
st.caption("AI-powered document intelligence for faster RFP analysis")
st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    from src.vector_store import get_collection_stats
    stats = get_collection_stats()
    docs = st.session_state.processed_docs

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documents", len(docs))
    col2.metric("Total Pages", sum(d["pages"] for d in docs.values()) if docs else 0)
    col3.metric("Total Chunks", stats["total_chunks"])
    col4.metric("Vector DB", "✅ Ready" if stats["total_chunks"] > 0 else "⬜ Empty")

    if docs:
        st.subheader("Indexed Documents")
        rows = [{"Document": k, "Pages": v["pages"], "Chunks": v["chunks"]} for k, v in docs.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No documents indexed yet. Go to **Upload RFP** to get started.")

    # Risk summary if available
    all_risks = []
    for r in st.session_state.risks.values():
        all_risks.extend(r)
    if all_risks:
        st.subheader("Risk Overview")
        severities = [r.get("severity", "Unknown") for r in all_risks]
        high = sum(1 for s in severities if "high" in s.lower())
        med = sum(1 for s in severities if "medium" in s.lower())
        low = sum(1 for s in severities if "low" in s.lower())
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 High Risks", high)
        c2.metric("🟡 Medium Risks", med)
        c3.metric("🟢 Low Risks", low)

# ═══════════════════════════════════════════════════════════════════════════
# HELPER: Document Processing
# ═══════════════════════════════════════════════════════════════════════════
def _process_document(uf):
    from src.pdf_processor import extract_pdf_pages, get_pdf_metadata
    from src.document_chunker import chunk_pages
    from src.vector_store import add_chunks, get_indexed_sources

    filepath = save_uploaded_file(uf, UPLOAD_DIRECTORY)
    h = file_hash(filepath)

    # Check if already processed
    if uf.name in st.session_state.processed_docs:
        if st.session_state.processed_docs[uf.name].get("hash") == h:
            st.info(f"'{uf.name}' is already indexed.")
            return

    with st.status(f"Processing {uf.name}...", expanded=True) as status:
        try:
            st.write("Extracting text from PDF...")
            pages = extract_pdf_pages(filepath)
            meta = get_pdf_metadata(filepath)

            empty_pages = [p["page"] for p in pages if not p["text"].strip()]
            if empty_pages:
                st.warning(f"Pages with no extractable text: {empty_pages}")

            st.write(f"Extracted {len(pages)} pages. Chunking...")
            chunks = chunk_pages(pages)

            st.write(f"Created {len(chunks)} chunks. Generating embeddings & indexing...")
            add_chunks(chunks)

            st.session_state.processed_docs[uf.name] = {
                "pages": meta["total_pages"],
                "chunks": len(chunks),
                "hash": h,
                "filepath": filepath,
            }
            status.update(label=f"✅ {uf.name} processed successfully!", state="complete")
        except ValueError as e:
            st.error(f"PDF Error: {e}")
            status.update(label="❌ Processing failed", state="error")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            logger.error(f"Processing error for {uf.name}: {e}")
            status.update(label="❌ Processing failed", state="error")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: UPLOAD
# ═══════════════════════════════════════════════════════════════════════════
if page == "📤 Upload RFP":
    st.subheader("Upload RFP Documents")
    uploaded_files = st.file_uploader(
        "Upload your RFP document(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more PDF files",
    )

    if uploaded_files:
        for uf in uploaded_files:
            st.markdown(f"**{uf.name}** — {uf.size / 1024:.1f} KB")
            if st.button(f"Process {uf.name}", key=f"proc_{uf.name}"):
                _process_document(uf)

    if st.session_state.processed_docs:
        st.divider()
        st.subheader("Processed Documents")
        for name, info in st.session_state.processed_docs.items():
            with st.expander(f"📄 {name}"):
                st.write(f"Pages: {info['pages']} | Chunks: {info['chunks']}")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: CHAT
# ═══════════════════════════════════════════════════════════════════════════
elif page == "💬 Chat / Q&A":
    from src.rag_pipeline import answer_question

    st.subheader("Chat with your RFP")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    # Document filter
    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Filter by document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc

    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "What is the objective of this project?",
            "What are the technical requirements?",
            "What are the security requirements?",
            "What compliance standards are mentioned?",
            "What are the project deliverables?",
            "What is the expected timeline?",
            "What are the evaluation criteria?",
            "What are the major risks?",
            "What information is missing from the RFP?",
            "What questions should we ask the client?",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                st.session_state["prefill_question"] = ex

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Sources"):
                    for s in msg["sources"]:
                        st.markdown(f"- **{s['source']}** — Page {s['page']}")

    # Input
    prefill = st.session_state.pop("prefill_question", "")
    question = st.chat_input("Ask a question about the RFP...")
    if not question and prefill:
        question = prefill

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing RFP..."):
                answer, sources = answer_question(question, source_filter=source_filter)
            st.markdown(answer)
            if sources:
                with st.expander("📎 Sources"):
                    for s in sources:
                        st.markdown(f"- **{s['source']}** — Page {s['page']}")

        st.session_state.chat_history.append({
            "role": "assistant", "content": answer, "sources": sources
        })

    if st.session_state.chat_history and st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📋 Executive Summary":
    from src.summarizer import generate_summary

    st.subheader("Executive Summary")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc
    cache_key = selected_doc

    if st.button("📋 Generate Executive Summary"):
        with st.spinner("Generating summary..."):
            summary = generate_summary(source_filter=source_filter)
            st.session_state.summary[cache_key] = summary

    if cache_key in st.session_state.summary:
        st.markdown(st.session_state.summary[cache_key])

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: REQUIREMENTS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📌 Requirements":
    from src.requirement_extractor import extract_requirements

    st.subheader("Requirement Extraction")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc
    cache_key = selected_doc

    if st.button("📌 Extract Requirements"):
        with st.spinner("Extracting requirements..."):
            reqs = extract_requirements(source_filter=source_filter)
            st.session_state.requirements[cache_key] = reqs

    if cache_key in st.session_state.requirements:
        reqs = st.session_state.requirements[cache_key]
        if reqs:
            df = pd.DataFrame(reqs)
            # Category filter
            if "category" in df.columns:
                cats = ["All"] + sorted(df["category"].unique().tolist())
                cat_filter = st.selectbox("Filter by category", cats)
                if cat_filter != "All":
                    df = df[df["category"] == cat_filter]
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total: {len(df)} requirements")
        else:
            st.info("No requirements extracted. Try re-running or check the document content.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: SECURITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔒 Security Analysis":
    from src.compliance_analyzer import analyze_security

    st.subheader("Security Analysis")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc
    cache_key = selected_doc

    if st.button("🔒 Run Security Analysis"):
        with st.spinner("Analyzing security requirements..."):
            findings = analyze_security(source_filter=source_filter)
            st.session_state.security[cache_key] = findings

    if cache_key in st.session_state.security:
        findings = st.session_state.security[cache_key]
        if findings:
            df = pd.DataFrame(findings)
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total: {len(df)} security findings")
        else:
            st.info("No explicit security requirements identified.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: COMPLIANCE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "✅ Compliance Analysis":
    from src.compliance_analyzer import analyze_compliance

    st.subheader("Compliance Analysis")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc
    cache_key = selected_doc

    if st.button("✅ Run Compliance Analysis"):
        with st.spinner("Analyzing compliance requirements..."):
            findings = analyze_compliance(source_filter=source_filter)
            st.session_state.compliance[cache_key] = findings

    if cache_key in st.session_state.compliance:
        findings = st.session_state.compliance[cache_key]
        if findings:
            df = pd.DataFrame(findings)
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total: {len(df)} compliance findings")
        else:
            st.info("No explicit compliance requirements identified.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: RISK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "⚠️ Risk Analysis":
    from src.risk_analyzer import analyze_risks

    st.subheader("Risk Analysis")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc
    cache_key = selected_doc

    if st.button("⚠️ Run Risk Analysis"):
        with st.spinner("Analyzing risks..."):
            risks = analyze_risks(source_filter=source_filter)
            st.session_state.risks[cache_key] = risks

    if cache_key in st.session_state.risks:
        risks = st.session_state.risks[cache_key]
        if risks:
            # Color-coded severity display
            severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            for r in risks:
                sev = r.get("severity", "").lower()
                icon = severity_color.get(sev, "⚪")
                with st.expander(f"{icon} [{r.get('category','Risk')}] {r.get('description','')[:80]}..."):
                    st.markdown(f"**Severity:** {r.get('severity','N/A')}")
                    st.markdown(f"**Evidence:** {r.get('evidence','N/A')}")
                    st.markdown(f"**Suggested Clarification:** {r.get('clarification','N/A')}")
        else:
            st.info("No risks identified.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: CLARIFICATION QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "❓ Clarification Questions":
    from src.clarification import generate_clarifications

    st.subheader("Client Clarification Questions")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc
    cache_key = selected_doc

    if st.button("❓ Generate Clarification Questions"):
        with st.spinner("Generating questions..."):
            questions = generate_clarifications(source_filter=source_filter)
            st.session_state.clarifications[cache_key] = questions

    if cache_key in st.session_state.clarifications:
        questions = st.session_state.clarifications[cache_key]
        if questions:
            df = pd.DataFrame(questions)
            if "group" in df.columns:
                for group in sorted(df["group"].unique()):
                    st.markdown(f"### {group}")
                    group_qs = df[df["group"] == group]["question"].tolist()
                    for i, q in enumerate(group_qs, 1):
                        st.markdown(f"{i}. {q}")
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No clarification questions generated.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: RFP COMPARISON
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔀 RFP Comparison":
    from src.comparison import compare_rfps

    st.subheader("RFP Comparison")

    docs = list(st.session_state.processed_docs.keys())
    if len(docs) < 2:
        st.warning("Please upload and process at least two RFP documents to compare.")
        st.stop()

    col1, col2 = st.columns(2)
    rfp_a = col1.selectbox("RFP A", docs, index=0)
    rfp_b = col2.selectbox("RFP B", docs, index=1)

    if rfp_a == rfp_b:
        st.warning("Please select two different documents.")
        st.stop()

    if st.button("🔀 Compare RFPs"):
        with st.spinner("Comparing documents..."):
            comparison = compare_rfps(rfp_a, rfp_b)
            st.session_state["comparison_result"] = comparison
            st.session_state["comparison_labels"] = (rfp_a, rfp_b)

    if "comparison_result" in st.session_state:
        result = st.session_state["comparison_result"]
        labels = st.session_state.get("comparison_labels", ("RFP A", "RFP B"))
        if result:
            df = pd.DataFrame(result)
            # Rename columns to actual doc names
            if "rfp_a" in df.columns:
                df = df.rename(columns={"rfp_a": labels[0], "rfp_b": labels[1]})
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No comparison data generated.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: EXPORT
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📥 Export":
    from src.exporter import export_excel, export_pdf_report

    st.subheader("Export Analysis")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Select document", doc_options)
    cache_key = selected_doc

    def _get(key):
        return st.session_state.get(key, {}).get(cache_key, [])

    summary_text = st.session_state.get("summary", {}).get(cache_key, "")
    reqs = _get("requirements")
    sec = _get("security")
    comp = _get("compliance")
    risks = _get("risks")
    clarifs = _get("clarifications")

    st.info("Run the analysis sections first to populate export data.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Export to Excel"):
            data = {
                "Requirements": reqs,
                "Security": sec,
                "Compliance": comp,
                "Risks": risks,
                "Clarifications": clarifs,
            }
            xlsx = export_excel(data)
            st.download_button(
                "⬇️ Download Excel",
                data=xlsx,
                file_name="rfp_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with col2:
        if st.button("📄 Export to PDF"):
            try:
                pdf_bytes = export_pdf_report(summary_text, reqs, sec, comp, risks, clarifs)
                st.download_button(
                    "⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name="rfp_analysis_report.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF export failed: {e}")
