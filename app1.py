import os
import json
import streamlit as st
from embedchain import App

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "vector_db")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
INDEX_FILE = os.path.join(BASE_DIR, "indexed_files.json")


def load_indexed_files():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_indexed_files(indexed_files):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(indexed_files)), f, indent=2)


@st.cache_resource
def get_embedchain_app(api_key: str):
    os.makedirs(DB_DIR, exist_ok=True)

    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "api_key": api_key,
                "model": "gpt-4o-mini"
            }
        },
        "vectordb": {
            "provider": "chroma",
            "config": {
                "dir": DB_DIR
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "api_key": api_key
            }
        }
    }

    return App.from_config(config=config)


def index_pdf(app, pdf_name, indexed_files):
    pdf_path = os.path.join(PDF_DIR, pdf_name)

    if pdf_name in indexed_files:
        return False, f"{pdf_name} already indexed."

    try:
        app.add(
            pdf_path,
            data_type="pdf_file",
            metadata={"source": pdf_name}
        )
        indexed_files.add(pdf_name)
        save_indexed_files(indexed_files)
        return True, f"✅ Added {pdf_name} to vector database."
    except Exception as e:
        return False, f"❌ Error indexing {pdf_name}: {e}"


# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Nigeria Election PDF Chat", layout="wide")
st.title("Chat on Nigeria Election Data")

# Read API key from Streamlit secrets
openai_access_token = st.secrets["OPENAI_API_KEY"]

# Ensure folders exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# Persistent record of indexed files
indexed_files = load_indexed_files()

# Create Embedchain app once
app = get_embedchain_app(openai_access_token)

with st.sidebar:
    st.header("📚 PDF Vector Database")

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        st.info("No PDFs found. Add PDF files to the /pdfs folder.")
    else:
        st.subheader("Available PDFs")
        for pdf_name in sorted(pdf_files):
            col1, col2 = st.columns([3, 1])

            with col1:
                status = "✅ Indexed" if pdf_name in indexed_files else "🕓 Not indexed"
                st.caption(f"{pdf_name} — {status}")

            with col2:
                if st.button(
                    "Add",
                    key=f"add_{pdf_name}",
                    disabled=(pdf_name in indexed_files)
                ):
                    success, message = index_pdf(app, pdf_name, indexed_files)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    st.divider()

    if st.button("Index all PDFs"):
        added = 0
        for pdf_name in pdf_files:
            if pdf_name not in indexed_files:
                success, _ = index_pdf(app, pdf_name, indexed_files)
                if success:
                    added += 1
        st.success(f"Indexed {added} new PDF(s).")

    if st.button("Refresh indexed file list"):
        indexed_files = load_indexed_files()
        st.success("Refreshed.")


st.subheader("Ask questions from the indexed PDFs")

question = st.text_input(
    "Enter your question",
    placeholder="Example: What does the election report say about voter turnout?"
)

if st.button("Ask"):
    if not indexed_files:
        st.warning("Please index at least one PDF first.")
    elif not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            answer = app.chat(question)
            st.markdown("### Answer")
            st.write(answer)
        except Exception as e:
            st.error(f"Error while querying vector database: {e}")


st.subheader("Current database status")
st.write(f"Indexed PDFs: {len(indexed_files)}")
if indexed_files:
    st.write(sorted(indexed_files))