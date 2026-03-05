import os
import tempfile
import streamlit as st
from embedchain import App

def embedchain_bot(db_path, api_key):
    return App.from_config(
        config={
            "llm": {"provider": "openai", "config": {"api_key": api_key}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
        }
    )

st.title("Chat with PDF")

#openai_access_token = st.text_input("OpenAI API Key", type="password")
openai_api_key = st.secrets["OOENAI_API_KEY"]
if openai_access_token:
    # Keep DB stable across reruns
    if "db_path" not in st.session_state:
        st.session_state.db_path = tempfile.mkdtemp()
    if "app" not in st.session_state:
        st.session_state.app = embedchain_bot(st.session_state.db_path, openai_access_token)

    app = st.session_state.app

    pdf_file = st.file_uploader("Upload a PDF file", type="pdf")

    if pdf_file:
        file_bytes = pdf_file.getvalue()

        # 1) Guard: empty upload
        if not file_bytes:
            st.error(f"'{pdf_file.name}' is empty (0 bytes). Please re-upload.")
            st.stop()

        # 2) Guard: not a real PDF
        if not file_bytes.startswith(b"%PDF"):
            st.error(f"'{pdf_file.name}' doesn't look like a valid PDF.")
            st.stop()

        # 3) Save to temp file and DO NOT delete immediately
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(file_bytes)
        tmp.close()

        try:
            app.add(tmp.name, data_type="pdf_file")
            st.success(f"Added {pdf_file.name} to knowledge base!")
            # store so you can optionally clean up later
            st.session_state.last_tmp_pdf = tmp.name
        except Exception as e:
            st.error(f"Failed to process PDF: {e}")
        # NOTE: don't os.remove(tmp.name) here

    prompt = st.text_input("Ask a question about the PDF")

    if prompt:
        answer = app.chat(prompt)
        st.write(answer)

    # Optional: cleanup button (delete after you're done chatting)
    if st.button("Clear uploaded temp PDF"):
        p = st.session_state.get("last_tmp_pdf")
        if p and os.path.exists(p):
            os.remove(p)
        st.success("Temp PDF cleared.")

    
