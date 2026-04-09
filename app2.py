import os
import streamlit as st
from embedchain import App

from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI


BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "vector_db")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")


# -----------------------------
# LLM Loader
# -----------------------------
def load_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=st.secrets["OPENAI_API_KEY"]
    )


# -----------------------------
# Embedchain (PDF search)
# -----------------------------
def embedchain_bot():
    return App.from_config(
        config={
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": st.secrets["OPENAI_API_KEY"],
                    "system_prompt": (
                        "Answer ONLY from the documents. "
                        "If the answer is not in the documents say: NOT_FOUND"
                    ),
                },
            },
            "vectordb": {
                "provider": "chroma",
                "config": {"dir": DB_DIR},
            },
            "embedder": {
                "provider": "openai",
                "config": {"api_key": st.secrets["OPENAI_API_KEY"]},
            },
        }
    )


# -----------------------------
# Web Agent (SerpAPI)
# -----------------------------
def create_web_agent():

    serp_api_key = st.secrets["SERPAPI_API_KEY"]

    search = SerpAPIWrapper(serpapi_api_key=serp_api_key)

    tools = [
        Tool(
            name="Web Search",
            func=search.run,
            description="Search the internet for up-to-date information"
        )
    ]

    agent = initialize_agent(
        tools=tools,
        llm=load_llm(),
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False
    )

    return agent


# -----------------------------
# Setup
# -----------------------------
st.title("Chat on Nigeria Election Data")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

if "app" not in st.session_state:
    st.session_state.app = embedchain_bot()

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = set()

app = st.session_state.app


# -----------------------------
# Auto index PDFs
# -----------------------------
pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

for pdf in pdf_files:
    if pdf not in st.session_state.indexed_files:
        path = os.path.join(PDF_DIR, pdf)
        app.add(path, data_type="pdf_file")
        st.session_state.indexed_files.add(pdf)


# -----------------------------
# Chat
# -----------------------------
prompt = st.text_input("Ask a question")

if prompt:

    with st.spinner("Searching documents..."):
        doc_answer = app.chat(prompt)

    # If document has answer
    if "NOT_FOUND" not in str(doc_answer):

        #st.markdown("### 📄 Answer from Documents")
        st.write(doc_answer)

    else:

        with st.spinner("Searching the internet..."):
            web_agent = create_web_agent()
            web_answer = web_agent.run(prompt)

        #st.markdown("### 🌍 Answer from Internet")
        st.write(web_answer)