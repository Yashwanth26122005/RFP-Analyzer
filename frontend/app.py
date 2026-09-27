import streamlit as st
import pandas as pd
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="GenAI-Powered RFP Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ───────────────────────────────────────────────────
for key, default in {
    "processed_docs": {},
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


def api(method, endpoint, **kwargs):
    try:
        resp = getattr(requests, method)(f"{API_URL}{endpoint}", **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure the API server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ── Sidebar ──────────────────────────────────────────────────────────────────
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
        for doc, info in st.session_state.processed_docs.items():
            st.markdown(f"- 📄 `{doc}` ({info['pages']}p)")

st.title("GenAI-Powered RFP Analyzer")
st.caption("AI-powered document intelligence for faster RFP analysis")
st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    data = api("get", "/stats")
    docs = st.session_state.processed_docs

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documents", len(docs))
    col2.metric("Total Pages", sum(d["pages"] for d in docs.values()) if docs else 0)
    col3.metric("Total Chunks", data["total_chunks"] if data else 0)
    col4.metric("Vector DB", "✅ Ready" if data and data["total_chunks"] > 0 else "⬜ Empty")

    if docs:
        st.subheader("Indexed Documents")
        rows = [{"Document": k, "Pages": v["pages"], "Chunks": v["chunks"]} for k, v in docs.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No documents indexed yet. Go to **Upload RFP** to get started.")

    all_risks = [r for v in st.session_state.risks.values() for r in v]
    if all_risks:
        st.subheader("Risk Overview")
        severities = [r.get("severity", "").lower() for r in all_risks]
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 High Risks", sum(1 for s in severities if "high" in s))
        c2.metric("🟡 Medium Risks", sum(1 for s in severities if "medium" in s))
        c3.metric("🟢 Low Risks", sum(1 for s in severities if "low" in s))


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: UPLOAD
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📤 Upload RFP":
    st.subheader("Upload RFP Documents")
    uploaded_files = st.file_uploader("Upload your RFP document(s)", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for uf in uploaded_files:
            st.markdown(f"**{uf.name}** — {uf.size / 1024:.1f} KB")
            if st.button(f"Process {uf.name}", key=f"proc_{uf.name}"):
                with st.spinner(f"Processing {uf.name}..."):
                    result = api("post", "/upload", files={"file": (uf.name, uf.getvalue(), "application/pdf")})
                if result:
                    st.session_state.processed_docs[uf.name] = {
                        "pages": result["pages"],
                        "chunks": result["chunks"],
                        "hash": result["hash"],
                    }
                    st.success(f"✅ {uf.name} processed — {result['pages']} pages, {result['chunks']} chunks")

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
    st.subheader("Chat with your RFP")

    if not st.session_state.processed_docs:
        st.warning("Please upload and process an RFP document first.")
        st.stop()

    doc_options = ["All Documents"] + list(st.session_state.processed_docs.keys())
    selected_doc = st.selectbox("Filter by document", doc_options)
    source_filter = None if selected_doc == "All Documents" else selected_doc

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
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                st.session_state["prefill_question"] = ex

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Sources"):
                    for s in msg["sources"]:
                        st.markdown(f"- **{s['source']}** — Page {s['page']}")

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
                result = api("post", "/chat", json={"question": question, "source_filter": source_filter})
            if result:
                st.markdown(result["answer"])
                if result.get("sources"):
                    with st.expander("📎 Sources"):
                        for s in result["sources"]:
                            st.markdown(f"- **{s['source']}** — Page {s['page']}")
                st.session_state.chat_history.append({
                    "role": "assistant", "content": result["answer"], "sources": result.get("sources", [])
                })

    if st.session_state.chat_history and st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📋 Executive Summary":
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
            result = api("post", "/summary", json={"source_filter": source_filter})
        if result:
            st.session_state.summary[cache_key] = result["summary"]

    if cache_key in st.session_state.summary:
        st.markdown(st.session_state.summary[cache_key])


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: REQUIREMENTS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📌 Requirements":
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
            result = api("post", "/requirements", json={"source_filter": source_filter})
        if result:
            st.session_state.requirements[cache_key] = result["requirements"]

    if cache_key in st.session_state.requirements:
        reqs = st.session_state.requirements[cache_key]
        if reqs:
            df = pd.DataFrame(reqs)
            if "category" in df.columns:
                cats = ["All"] + sorted(df["category"].unique().tolist())
                cat_filter = st.selectbox("Filter by category", cats)
                if cat_filter != "All":
                    df = df[df["category"] == cat_filter]
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total: {len(df)} requirements")
        else:
            st.info("No requirements extracted.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: SECURITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔒 Security Analysis":
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
            result = api("post", "/security", json={"source_filter": source_filter})
        if result:
            st.session_state.security[cache_key] = result["findings"]

    if cache_key in st.session_state.security:
        findings = st.session_state.security[cache_key]
        if findings:
            st.dataframe(pd.DataFrame(findings), use_container_width=True)
            st.caption(f"Total: {len(findings)} security findings")
        else:
            st.info("No explicit security requirements identified.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: COMPLIANCE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "✅ Compliance Analysis":
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
            result = api("post", "/compliance", json={"source_filter": source_filter})
        if result:
            st.session_state.compliance[cache_key] = result["findings"]

    if cache_key in st.session_state.compliance:
        findings = st.session_state.compliance[cache_key]
        if findings:
            st.dataframe(pd.DataFrame(findings), use_container_width=True)
            st.caption(f"Total: {len(findings)} compliance findings")
        else:
            st.info("No explicit compliance requirements identified.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: RISK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "⚠️ Risk Analysis":
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
            result = api("post", "/risks", json={"source_filter": source_filter})
        if result:
            st.session_state.risks[cache_key] = result["risks"]

    if cache_key in st.session_state.risks:
        risks = st.session_state.risks[cache_key]
        if risks:
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
            result = api("post", "/clarifications", json={"source_filter": source_filter})
        if result:
            st.session_state.clarifications[cache_key] = result["questions"]

    if cache_key in st.session_state.clarifications:
        questions = st.session_state.clarifications[cache_key]
        if questions:
            df = pd.DataFrame(questions)
            if "group" in df.columns:
                for group in sorted(df["group"].unique()):
                    st.markdown(f"### {group}")
                    for i, q in enumerate(df[df["group"] == group]["question"].tolist(), 1):
                        st.markdown(f"{i}. {q}")
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No clarification questions generated.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: RFP COMPARISON
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔀 RFP Comparison":
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
            result = api("post", "/compare", json={"source_a": rfp_a, "source_b": rfp_b})
        if result:
            st.session_state["comparison_result"] = result["comparison"]
            st.session_state["comparison_labels"] = (rfp_a, rfp_b)

    if "comparison_result" in st.session_state:
        result = st.session_state["comparison_result"]
        labels = st.session_state.get("comparison_labels", ("RFP A", "RFP B"))
        if result:
            df = pd.DataFrame(result)
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
            data = {"Requirements": reqs, "Security": sec, "Compliance": comp, "Risks": risks, "Clarifications": clarifs}
            xlsx = export_excel(data)
            st.download_button("⬇️ Download Excel", data=xlsx, file_name="rfp_analysis.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col2:
        if st.button("📄 Export to PDF"):
            try:
                pdf_bytes = export_pdf_report(summary_text, reqs, sec, comp, risks, clarifs)
                st.download_button("⬇️ Download PDF Report", data=pdf_bytes, file_name="rfp_analysis_report.pdf",
                                   mime="application/pdf")
            except Exception as e:
                st.error(f"PDF export failed: {e}")
