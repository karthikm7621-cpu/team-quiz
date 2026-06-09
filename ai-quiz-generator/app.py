import os
import io
import json
import csv
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from pypdf import PdfReader

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'csv'}

API_KEY = os.environ.get('GEMINI_API_KEY')
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable must be set")

client = genai.Client(api_key=API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_txt(file_content):
    return file_content.decode('utf-8')

def extract_text_from_csv(file_content):
    text = ""
    lines = file_content.decode('utf-8').strip().split('\n')
    reader = csv.reader(lines)
    for row in reader:
        text += ' '.join(row) + '\n'
    return text

def extract_text_from_pdf(file_content):
    reader = PdfReader(io.BytesIO(file_content))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_file(file_content, filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        return extract_text_from_txt(file_content)
    elif ext == 'csv':
        return extract_text_from_csv(file_content)
    elif ext == 'pdf':
        return extract_text_from_pdf(file_content)
    elif ext in {'png', 'jpg', 'jpeg'}:
        mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=file_content, mime_type=mime_type),
                "Extract all readable text from this image. Return only the extracted text, nothing else."
            ]
        )
        return response.text
    return ""

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
    text_content = ""
    
    if 'file' in request.files and request.files['file']:
        file = request.files['file']
        if file and allowed_file(file.filename):
            file_content = file.read()
            text_content = extract_text_from_file(file_content, file.filename)
        else:
            return jsonify({"error": "Invalid file type"}), 400
    elif 'text' in request.form and request.form['text']:
        text_content = request.form['text']
    else:
        return jsonify({"error": "No text or file provided"}), 400
    
    num_questions = int(request.form.get('num_questions', 10))
    
    quiz_prompt = f"""Generate {num_questions} multiple-choice quiz questions based on the following text.
Each question must have exactly 4 options and a correct_index (0-3) indicating the correct option.
Return ONLY valid JSON array.
Text: {text_content}"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=quiz_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=quiz_schema
            )
        )
        parsed = json.loads(response.text) if isinstance(response.text, str) else response.text
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)