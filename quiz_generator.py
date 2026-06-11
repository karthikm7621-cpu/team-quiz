import io
import json
import csv
import logging
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if not API_KEY:
    logger.warning('GEMINI_API_KEY or GOOGLE_API_KEY not found in environment')
    client = None
else:
    try:
        client = genai.Client(api_key=API_KEY)
        logger.info('Gemini client initialized successfully')
    except Exception as e:
        logger.error(f'Failed to initialize Gemini client: {e}')
        client = None

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'csv'}

quiz_schema = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'question': {'type': 'string'},
            'options': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 4, 'maxItems': 4},
            'correct_index': {'type': 'integer'},
            'explanation': {'type': 'string'}
        },
        'required': ['question', 'options', 'correct_index', 'explanation']
    }
}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_txt(file_content: bytes) -> str:
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        return file_content.decode('latin-1')


def extract_text_from_csv(file_content: bytes) -> str:
    decoded = None
    for encoding in ('utf-8', 'latin-1'):
        try:
            decoded = file_content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        raise ValueError('Unable to read CSV file')

    text_lines = []
    reader = csv.reader(decoded.strip().splitlines())
    for row in reader:
        text_lines.append(' '.join(row))
    return '\n'.join(text_lines)


def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_content))
        if not reader.pages:
            raise ValueError('PDF file is empty or invalid')

        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)

        text = '\n'.join(pages_text)
        if not text.strip():
            raise ValueError('No readable text was extracted from the PDF.')
        return text
    except Exception as e:
        logger.error(f'PDF extraction failed: {e}')
        raise ValueError(f'PDF extraction failed: {e}')


def extract_text_from_image(file_content: bytes, ext: str) -> str:
    if client is None:
        raise ValueError('Image OCR requires GEMINI_API_KEY or GOOGLE_API_KEY to be configured')

    mime_type = f'image/{ext}' if ext != 'jpg' else 'image/jpeg'
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                types.Part.from_bytes(data=file_content, mime_type=mime_type),
                'Extract all readable text from this image. Return only the extracted text, nothing else.'
            ]
        )
        if not response.text:
            raise ValueError('No text extracted from image')
        return response.text
    except Exception as e:
        logger.error(f'Image OCR failed: {e}')
        raise ValueError(f'Image OCR failed: {e}')


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    if not allowed_file(filename):
        raise ValueError('Unsupported file type')

    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        return extract_text_from_txt(file_content)
    if ext == 'csv':
        return extract_text_from_csv(file_content)
    if ext == 'pdf':
        return extract_text_from_pdf(file_content)
    if ext in {'png', 'jpg', 'jpeg'}:
        return extract_text_from_image(file_content, ext)
    raise ValueError('Unsupported file type')


def build_quiz_prompt(text_content: str, num_questions: int) -> str:
    return f"""
Generate {num_questions} multiple-choice quiz questions based on the following text.
Each question must have exactly 4 options and a correct_index (0-3) indicating the correct option.
Return ONLY valid JSON array.
Text: {text_content}
"""


def generate_quiz(text_content: str, num_questions: int = 10):
    if client is None:
        raise RuntimeError('GEMINI_API_KEY or GOOGLE_API_KEY is not configured')

    if not text_content or not text_content.strip():
        raise ValueError('Input text is empty')

    num_questions = max(1, min(20, int(num_questions)))
    prompt = build_quiz_prompt(text_content, num_questions)

    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=quiz_schema
        )
    )

    if not response.text:
        raise ValueError('Empty response from AI model')

    try:
        parsed = json.loads(response.text) if isinstance(response.text, str) else response.text
    except json.JSONDecodeError as e:
        logger.error(f'JSON parsing failed: {e}')
        raise ValueError('Invalid response format from AI model')

    if not isinstance(parsed, list):
        raise ValueError('Response was not a valid JSON array')

    return parsed
