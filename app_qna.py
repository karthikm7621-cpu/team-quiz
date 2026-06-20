import os
from pathlib import Path

import streamlit as st

from rag_workflow import (
    create_vector_store,
    extract_text_chunks,
    generate_answer,
    get_embedding_model,
    get_llm,
    retrieve_context,
)

# --- UI Setup ---
st.set_page_config(page_title="Document Q&A", layout="wide")
st.title("📄 Local-First Document Q&A")
st.markdown(
    """
    *Powered by `PyMuPDF4LLM`, `SentenceTransformers`, `FAISS`, and `Llama.cpp`*

    **Instructions:**
    1.  Upload a PDF document.
    2.  Wait for it to be processed.
    3.  Ask a question about the document's content.

    *Note: The entire process runs locally on your machine. Your data is never sent to an external server.*
"""
)

# --- State Management ---
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "doc_filename" not in st.session_state:
    st.session_state.doc_filename = None

# --- Sidebar for Document Upload ---
with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf", accept_multiple_files=False)

    if uploaded_file:
        # Avoid reprocessing the same file
        if uploaded_file.name != st.session_state.doc_filename:
            st.session_state.doc_filename = uploaded_file.name

            # Save the file temporarily
            temp_dir = Path("temp_docs")
            temp_dir.mkdir(exist_ok=True)
            file_path = temp_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner(f"Processing {uploaded_file.name}..."):
                st.session_state.chunks = extract_text_chunks(file_path)

                if not st.session_state.chunks:
                    st.error("Could not extract text from the PDF.")
                else:
                    embedding_model = get_embedding_model()
                    st.session_state.vector_store = create_vector_store(st.session_state.chunks, embedding_model)
                    st.success(f"✅ Ready to answer questions about **{uploaded_file.name}**")
        else:
            st.info(f"✅ **{uploaded_file.name}** is already loaded.")


# --- Main Area for Q&A ---
st.header("2. Ask a Question")

if st.session_state.vector_store is None:
    st.warning("Please upload a document in the sidebar to begin.")
else:
    embedding_model = get_embedding_model()
    llm = get_llm()

    question = st.text_input("Enter your question here:", placeholder="e.g., What are the main conclusions of the document?")

    if st.button("Ask"):
        if not question:
            st.error("Please enter a question.")
        elif llm is None:
            st.error("The local LLM is not loaded. Please check the model path and configuration.")
        else:
            context = retrieve_context(question, st.session_state.vector_store, st.session_state.chunks, embedding_model)
            answer = generate_answer(question, context, llm)
            st.subheader("Answer:")
            st.markdown(answer)