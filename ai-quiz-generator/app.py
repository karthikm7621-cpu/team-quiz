import os
import io
import json
import csv
import logging
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from pypdf import PdfReader
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'csv'}

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_txt(file_content):
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return file_content.decode('latin-1')
        except Exception as e:
            logger.error(f'Failed to decode text file: {e}')
            raise ValueError('Unable to read text file encoding')

def extract_text_from_csv(file_content):
    try:
        text = ""
        lines = file_content.decode('utf-8').strip().split('\n')
        reader = csv.reader(lines)
        for row in reader:
            text += ' '.join(row) + '\n'
        return text
    except UnicodeDecodeError:
        try:
            text = ""
            lines = file_content.decode('latin-1').strip().split('\n')
            reader = csv.reader(lines)
            for row in reader:
                text += ' '.join(row) + '\n'
            return text
        except Exception as e:
            logger.error(f'Failed to parse CSV: {e}')
            raise ValueError('Unable to read CSV file')

def extract_text_from_pdf(file_content):
    try:
        reader = PdfReader(io.BytesIO(file_content))
        if len(reader.pages) == 0:
            raise ValueError("PDF file is empty or invalid")
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text.strip():
            raise ValueError("No text could be extracted from PDF. It may be scanned images or password protected.")
        return text
    except Exception as e:
        logger.error(f'PDF extraction failed: {e}')
        raise ValueError(f'PDF processing failed: {str(e)}')

def extract_text_from_image(file_content, ext):
    if client is None:
        raise ValueError('Image OCR requires GEMINI_API_KEY to be configured in .env file')
    mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=file_content, mime_type=mime_type),
                "Extract all readable text from this image. Return only the extracted text, nothing else."
            ]
        )
        if not response.text:
            raise ValueError("No text extracted from image")
        return response.text
    except Exception as e:
        logger.error(f'Image OCR failed: {e}')
        raise ValueError(f'Image processing failed: {str(e)}')

def extract_text_from_file(file_content, filename):
    try:
        ext = filename.rsplit('.', 1)[1].lower()
        if ext == 'txt':
            return extract_text_from_txt(file_content)
        elif ext == 'csv':
            return extract_text_from_csv(file_content)
        elif ext == 'pdf':
            return extract_text_from_pdf(file_content)
        elif ext in {'png', 'jpg', 'jpeg'}:
            return extract_text_from_image(file_content, ext)
        return ""
    except ValueError:
        raise
    except Exception as e:
        logger.error(f'Unexpected file extraction error: {e}')
        raise ValueError(f'Failed to process file: {str(e)}')

quiz_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "options": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
            "correct_index": {"type": "integer"},
            "explanation": {"type": "string"}
        },
        "required": ["question", "options", "correct_index", "explanation"]
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    if client is None:
        return jsonify({
            'status': 'error',
            'message': 'API key not configured. Please add GEMINI_API_KEY to your .env file and restart the server.',
            'code': 'MISSING_API_KEY'
        }), 400
    
    try:
        text_content = ""
        
        if 'file' in request.files and request.files['file']:
            file = request.files['file']
            if file and allowed_file(file.filename):
                file_content = file.read()
                text_content = extract_text_from_file(file_content, file.filename)
            else:
                return jsonify({'status': 'error', 'message': 'Invalid file type. Supported: PDF, PNG, JPG, TXT, CSV'}), 400
        elif 'text' in request.form and request.form['text']:
            text_content = request.form['text']
        else:
            return jsonify({'status': 'error', 'message': 'No text or file provided'}), 400
        
        if not text_content or not text_content.strip():
            return jsonify({'status': 'error', 'message': 'Empty or invalid input content'}), 400
        
        num_questions_raw = request.form.get('num_questions', '10')
        try:
            num_questions = int(num_questions_raw)
            num_questions = max(1, min(20, num_questions))
        except (ValueError, TypeError):
            num_questions = 10
        
        quiz_prompt = """
Generate {} multiple-choice quiz questions based on the following text.
Each question must have exactly 4 options and a correct_index (0-3) indicating the correct option.
Return ONLY valid JSON array.
Text: {}
""".format(num_questions, text_content)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=quiz_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=quiz_schema
            )
        )
        
        if not response.text:
            raise ValueError("Empty response from AI model")
        
        try:
            if isinstance(response.text, str):
                parsed = json.loads(response.text)
            else:
                parsed = response.text
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError("Invalid response format from AI model")
        
        if not isinstance(parsed, list):
            raise ValueError("Response was not a valid JSON array")
        
        return jsonify({'status': 'success', 'questions': parsed})
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.exception("Unexpected error in generate_quiz")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred. Check server logs.'}), 500

@app.route('/check-api-key', methods=['GET'])
def check_api_key():
    return jsonify({'configured': client is not None})

@app.errorhandler(404)
def not_found(e):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'status': 'error', 'message': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.exception('Internal server error')
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)