import os
import shutil
import streamlit as st
from embedchain import App

BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "vector_db")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")  # put PDFs here

def embedchain_bot(db_path: str, api_key: str) -> App:
    os.makedirs(db_path, exist_ok=True)
    return App.from_config(
        config={
            "llm": {"provider": "openai", "config": {"api_key": api_key}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
        }
    )

st.title("Chat with PDFs - Vector Database")

# Use Streamlit Cloud secrets
openai_access_token = st.secrets["OPENAI_API_KEY"]

# Ensure folders exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# Create app once per session
if "app" not in st.session_state:
    st.session_state.app = embedchain_bot(DB_DIR, openai_access_token)

# Track indexed files in this session
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = set()

app = st.session_state.app

with st.sidebar:
    st.header("📚 Vector Database")

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        st.info("No PDFs found. Add PDFs to the /pdfs folder in your repo.")
    else:
        st.subheader("Available PDFs in /pdfs")
        for pdf_name in sorted(pdf_files):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.caption(pdf_name)

            with col2:
                already = pdf_name in st.session_state.indexed_files
                if st.button("Add", key=f"add_{pdf_name}", disabled=already):
                    pdf_path = os.path.join(PDF_DIR, pdf_name)
                    try:
                        app.add(pdf_path, data_type="pdf_file", metadata={"source": pdf_name})
                        st.session_state.indexed_files.add(pdf_name)
                        st.success(f"✅ Added {pdf_name}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    if st.session_state.indexed_files:
        st.subheader("Indexed (this session)")
        for f in sorted(st.session_state.indexed_files):
            st.caption(f"✔️ {f}")

    if st.button("🗑️ Clear Database"):
        shutil.rmtree(DB_DIR, ignore_errors=True)
        os.makedirs(DB_DIR, exist_ok=True)
        st.session_state.indexed_files = set()
        st.session_state.app = embedchain_bot(DB_DIR, openai_access_token)
        st.success("Database cleared!")

# Main chat
if st.session_state.indexed_files:
    prompt = st.text_input("Ask a question about your documents")
    if prompt:
        st.write(app.chat(prompt))
else:
    st.info("👈 Add PDFs from the sidebar to start chatting!")