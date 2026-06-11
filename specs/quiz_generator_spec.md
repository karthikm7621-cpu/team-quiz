# Specification: Quiz Generation Engine

## Overview
This specification details the functionality of the `quiz_generator.py` module. This module is the core engine responsible for parsing input text from various file formats and generating quiz questions, either through a local heuristic-based method or via the Gemini AI API.

## Technical Requirements
- **File Parsing**: Must handle text extraction from PDF, TXT, CSV, and various common text-based formats. Image OCR is an optional, best-effort feature.
- **Quiz Generation Modes**:
    - **Local Mode**: Generates questions using sentence and keyword analysis from the source text. This mode must function entirely offline.
    - **AI-Powered Mode**: Interfaces with the Google Gemini API to generate higher-quality, context-aware questions based on a detailed prompt.
- **Configuration**: Question generation must be configurable by number of questions, question type, difficulty, and desired answer length.
- **Output**: All generation functions must return a list of dictionaries, where each dictionary represents a single, well-structured question object.

## Acceptance Criteria

### `extract_text_from_file()`
- [x] Given a `.txt` file, returns its decoded string content.
- [x] Given a `.pdf` file, returns the extracted text from all pages.
- [x] Given a `.csv` file, returns a string with rows concatenated.
- [ ] Given an unsupported file type, raises a `ValueError`.

### `generate_quiz()` (Local Mode)
- [x] Given text content and parameters, returns the specified number of questions.
- [x] Each generated question dictionary contains `type`, `question`, `points`, `answer`, and `explanation`.
- [x] For `MCQ` type, the question object also contains `options` (list) and `correct_index` (int).
- [ ] If input text is empty or too short, returns an empty list.

### `generate_ai_quiz()` (AI-Powered Mode)
- [x] Given text content and an API key, returns a list of question objects from the Gemini API.
- [x] If the API key is missing, raises a `ValueError`.
- [x] Handles API errors (e.g., rate limits, invalid JSON response) with retries and graceful failure.
- [x] The output JSON from the API is correctly parsed into the standard question dictionary format.

## Security & Compliance
- **API Keys**: The Gemini API key must not be hardcoded and should be handled securely (e.g., via environment variables).
- **Input Sanitization**: While the primary input is text for analysis, ensure that file handling does not introduce path traversal or other file-based vulnerabilities.
- **Data Privacy**: When using AI mode, be aware that content is sent to a third-party service.