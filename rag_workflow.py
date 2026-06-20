import os
from pathlib import Path

import faiss
import numpy as np
import pymupdf4llm  # Using the requested library
import streamlit as st
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer


# --- 1. Document Loading and Chunking ---
def extract_text_chunks(file_path: Path) -> list[str]:
    """Extracts text from a PDF and splits it into semantic chunks using PyMuPDF4LLM."""
    try:
        # to_markdown preserves layout and structure, which is good for context.
        md_text = pymupdf4llm.to_markdown(str(file_path))

        # Split the markdown text into chunks. Splitting by paragraphs is a good start.
        chunks = md_text.split("\n\n")

        # Clean up and filter chunks for meaningful content
        processed_chunks = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 100]
        if not processed_chunks:
            # Fallback for documents without many double newlines
            return [md_text]
        return processed_chunks
    except Exception as e:
        st.error(f"Error processing PDF with PyMuPDF4LLM: {e}")
        return []


# --- 2. Embedding and Vector Storage ---
@st.cache_resource
def get_embedding_model():
    """Loads a sentence-transformer model from Hugging Face."""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


def create_vector_store(chunks: list[str], model):
    """Creates a FAISS vector store from text chunks."""
    if not chunks:
        return None
    with st.spinner("Creating embeddings for the document..."):
        embeddings = model.encode(chunks, convert_to_tensor=False, show_progress_bar=True)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype("float32"))
    return index


# --- 3. Retrieval ---
def retrieve_context(query: str, index, chunks: list[str], model, top_k=3) -> str:
    """Retrieves the most relevant text chunks from the vector store."""
    if index is None:
        return ""
    query_embedding = model.encode([query])
    _, indices = index.search(np.array(query_embedding).astype("float32"), top_k)

    context = "\n---\n".join([chunks[i] for i in indices[0] if i < len(chunks)])
    return context


# --- 4. Answer Generation ---
@st.cache_resource
def get_llm():
    """Loads the Llama.cpp model."""
    # --- IMPORTANT ---
    # 1. Download a GGUF model (e.g., from https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
    # 2. Place it in a directory (e.g., 'models/')
    # 3. Update the 'model_path' below or set the `LOCAL_LLM_PATH` environment variable.
    model_path_str = os.getenv("LOCAL_LLM_PATH", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    model_path = Path(model_path_str)

    if not model_path.exists():
        st.error(
            f"LLM model not found at '{model_path}'. Please update the path in `rag_workflow.py` "
            f"or set the `LOCAL_LLM_PATH` environment variable."
        )
        return None

    try:
        # Offload all layers to GPU if available
        llm = Llama(model_path=str(model_path), n_ctx=4096, n_gpu_layers=-1, verbose=False)
        return llm
    except Exception as e:
        st.error(f"Failed to load LLM. Ensure `llama-cpp-python` is installed correctly for your system.\nError: {e}")
        return None


def generate_answer(query: str, context: str, llm) -> str:
    """Generates an answer using the LLM with the provided context."""
    if llm is None:
        return "LLM not loaded. Cannot generate an answer."

    # A prompt template for instruction-tuned models
    prompt = f"""
    [INST] You are a question-answering assistant. Use the provided document context to answer the question accurately.
    - Answer based only on the information within the context.
    - If the context does not contain the answer, state that the answer is not available in the document.

    CONTEXT:
    {context}

    QUESTION: {query}
    [/INST]
    """

    with st.spinner("🤖 Generating answer..."):
        output = llm(prompt, max_tokens=512, stop=["[INST]", "QUESTION:"])

    answer = output["choices"][0]["text"].strip()
    return answer