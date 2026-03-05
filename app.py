import os
import streamlit as st
from embedchain import App

# Create persistent database directory
DB_DIR = os.path.join(os.path.dirname(__file__), "vector_db")
PDF_DIR = os.path.dirname(__file__)

def embedchain_bot(db_path, api_key):
    return App.from_config(
        config={
            "llm": {"provider": "openai", "config": {"api_key": api_key}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
        }
    )

st.title("Chat with PDF - Vector Database")

#openai_access_token = st.text_input("OpenAI API Key", type="password")
openai_access_token = st.secrets["OPENAI_API_KEY"]
if openai_access_token:
    # Create persistent database (not temporary)
    if "db_path" not in st.session_state:
        os.makedirs(DB_DIR, exist_ok=True)
        st.session_state.db_path = DB_DIR
    
    if "app" not in st.session_state:
        st.session_state.app = embedchain_bot(st.session_state.db_path, openai_access_token)
        st.session_state.indexed_files = set()

    app = st.session_state.app

    # Sidebar: Manage Vector Database
    with st.sidebar:
        st.header("📚 Vector Database")
        
        # Find available PDFs
        pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
        
        if pdf_files:
            st.subheader("Available PDFs")
            for pdf_file in pdf_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(pdf_file)
                with col2:
                    if st.button("Add", key=pdf_file):
                        pdf_path = os.path.join(PDF_DIR, pdf_file)
                        try:
                            app.add(pdf_path, data_type="pdf_file")
                            st.session_state.indexed_files.add(pdf_file)
                            st.success(f"✅ Added {pdf_file}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
        else:
            st.info("No PDF files found in app directory")
        
        # Show indexed files
        if st.session_state.indexed_files:
            st.subheader("Indexed Files")
            for file in st.session_state.indexed_files:
                st.caption(f"✔️ {file}")
        
        # Clear database button
        if st.button("🗑️ Clear Database"):
            import shutil
            if os.path.exists(DB_DIR):
                shutil.rmtree(DB_DIR)
                os.makedirs(DB_DIR, exist_ok=True)
            st.session_state.indexed_files = set()
            st.session_state.app = embedchain_bot(st.session_state.db_path, openai_access_token)
            st.success("Database cleared!")

    # Main chat interface
    if st.session_state.indexed_files:
        prompt = st.text_input("Ask a question about your documents")

        if prompt:
            answer = app.chat(prompt)
            st.write(answer)
    else:
        st.info("👈 Add PDFs from the sidebar to start chatting!")