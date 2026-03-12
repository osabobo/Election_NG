import os
import streamlit as st
from embedchain import App

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "vector_db")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")


@st.cache_resource
def get_app(api_key: str):
    os.makedirs(DB_DIR, exist_ok=True)

    return App.from_config(
        config={
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": api_key,
                    "model": "gpt-4o-mini",
                },
            },
            "vectordb": {
                "provider": "chroma",
                "config": {
                    "dir": DB_DIR,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "api_key": api_key,
                },
            },
        }
    )


def auto_index_pdfs(app):
    if not os.path.exists(PDF_DIR):
        return

    pdf_files = [
        os.path.join(PDF_DIR, f)
        for f in os.listdir(PDF_DIR)
        if f.lower().endswith(".pdf")
    ]

    for pdf_path in pdf_files:
        try:
            app.add(pdf_path, data_type="pdf_file")
        except Exception:
            pass


# ---------------- STREAMLIT APP ----------------
st.set_page_config(page_title="Nigeria Election AI", layout="centered")
st.title("Nigeria Election Data AI Assistant")

openai_access_token = st.secrets["OPENAI_API_KEY"]

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# Initialize vector database app
app = get_app(openai_access_token)

# Automatically index PDFs once per session
if "indexed" not in st.session_state:
    with st.spinner("Preparing election knowledge base..."):
        auto_index_pdfs(app)
    st.session_state.indexed = True

# Chat interface
st.subheader("Ask a question")

question = st.text_input(
    "Ask anything about Nigeria election data",
    placeholder="Example: What was the voter turnout in the 2023 election?"
)

if st.button("Ask"):
    if question.strip():
        try:
            response = app.chat(question)

            st.markdown("### Answer")
            st.write(response)

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a question.")