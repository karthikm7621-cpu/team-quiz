import io
import csv
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    "pdf", "txt", "csv", "md", "json", "py", "js", "html", "css",
    "png", "jpg", "jpeg", # For OCR
    "docx", "pptx", "xlsx" # For document intelligence
}

def allowed_file(filename: str) -> bool:
    """Checks if the file extension is supported."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in SUPPORTED_EXTENSIONS

def extract_text_from_txt(file_content: bytes) -> str:
    """Tries to decode text content with common encodings."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_content.decode(enc)
        except UnicodeDecodeError:
            continue
    return file_content.decode("utf-8", errors="ignore")

def extract_text_from_csv(file_content: bytes) -> str:
    """Extracts content from a CSV file, preserving rows."""
    decoded = extract_text_from_txt(file_content)
    try:
        reader = csv.reader(decoded.strip().splitlines())
        return "\n".join([" ".join(row) for row in reader])
    except Exception:
        return decoded # Fallback to plain text extraction

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(io.BytesIO(file_content))
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

def extract_text_from_image(file_content: bytes) -> str:
    """Extracts text from an image using OCR (requires tesseract)."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(file_content))
        return pytesseract.image_to_string(image)
    except ImportError:
        logger.warning("OCR requires `pytesseract` and a Tesseract installation.")
        return "[OCR not configured]"
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return ""

def extract_text_from_docx(file_content: bytes) -> str:
    """Extracts text from a DOCX file."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        logger.warning("DOCX parsing requires the `python-docx` library.")
        return "[DOCX parser not installed]"
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Unified function to extract text from various file types.
    This acts as the content extraction pipeline.
    """
    ext = filename.rsplit(".", 1)[1].lower()
    
    if not allowed_file(filename):
        raise ValueError(f"Unsupported file type: .{ext}")

    extraction_map = {
        "pdf": extract_text_from_pdf,
        "csv": extract_text_from_csv,
        "png": extract_text_from_image,
        "jpg": extract_text_from_image,
        "jpeg": extract_text_from_image,
        "docx": extract_text_from_docx,
    }

    # Use specific extractor if available, otherwise fallback to generic text
    extractor = extraction_map.get(ext, extract_text_from_txt)
    
    return extractor(file_content)