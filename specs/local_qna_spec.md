# Feature: Local-First Document Q&A

## Overview
This feature implements a Retrieval-Augmented Generation (RAG) workflow that runs entirely on the user's local machine. It allows users to upload a document (PDF) and ask questions about its content without any data leaving their computer, ensuring privacy and offline capability.

## User Story
- As a user, I want to upload a PDF document and ask questions about its contents using a local AI model, so that I can get answers without an internet connection and without sending my private data to a third-party service.

## Technical Requirements
- **Document Parsing**: Use `pymupdf4llm` to extract structured text (Markdown) from uploaded PDF files.
- **Text Chunking**: Segment the extracted text into manageable chunks for embedding.
- **Embeddings**: Use the `sentence-transformers` library with a lightweight local model (e.g., `all-MiniLM-L6-v2`) to generate vector embeddings for the text chunks.
- **Vector Storage**: Use `faiss-cpu` as a local, in-memory vector store for efficient similarity search.
- **LLM**: Use `llama-cpp-python` to run a GGUF-formatted Large Language Model (e.g., Mistral 7B) locally for answer generation.
- **UI**: Integrate the workflow into the Streamlit application with a new "Document Q&A" section.
- **Configuration**: The path to the local LLM model file should be configurable, ideally via an environment variable.

## Acceptance Criteria
- [ ] The app provides a new interface for document Q&A.
- [ ] A user can upload a PDF file.
- [ ] The application processes the PDF, creates embeddings, and builds a vector index locally.
- [ ] The user can type a question into a text input field.
- [ ] The application retrieves relevant context from the document and uses a local LLM to generate an answer.
- [ ] The generated answer is displayed in the UI.
- [ ] The entire process works offline (after initial model downloads).
- [ ] Clear instructions are provided to the user on how to set up the local LLM model.