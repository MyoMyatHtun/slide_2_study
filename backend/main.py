from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz  # PyMuPDF
import re
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

app = FastAPI()

# CORS for React frontend (adjust origin if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# LOAD MODEL ON STARTUP
# ==========================================
MODEL_PATH = "./model"
print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
print("Model loaded.")

# ==========================================
# DATA MODELS
# ==========================================
class SummaryResponse(BaseModel):
    summary: str
    wordCount: int

class TextInput(BaseModel):
    text: str

class ExtractResponse(BaseModel):
    text: str
    wordCount: int

# ==========================================
# PDF EXTRACTION (WORDS + FORMULAS ONLY)
# ==========================================

# Regex patterns for mathematical formulas
MATH_PATTERNS = [
    r'\$[^$]+\$',                     # LaTeX inline math: $...$
    r'\\[a-zA-Z]+',                   # LaTeX commands: \alpha, \sum
    r'[a-zA-Z]+\^\{[^}]+\}',          # Superscript: x^{2}
    r'[a-zA-Z]+\_[^}]+',              # Subscript: x_{2}
    r'[a-zA-Z]+\^[0-9]',              # Simple superscript: x^2
    r'[a-zA-Z]+\_[0-9]',              # Simple subscript: x_2
    r'[0-9]+[+\-*/=][0-9]+',          # Simple equations: 2+2=4
    r'[a-zA-Z][+\-*/=][a-zA-Z]',      # Variable equations: x+y=z
    r'[0-9]+\.[0-9]+',                # Decimal numbers
    r'[0-9]+[eE][+\-]?[0-9]+',        # Scientific notation
]

# Combine patterns into one regex
MATH_REGEX = re.compile('|'.join(MATH_PATTERNS), re.IGNORECASE)

# Unicode math symbols
MATH_SYMBOLS = set('∫∑∏√∂∞≈≠≤≥×÷±∈∉⊂⊆∪∩∀∃αβγδεθλμπσω')

def extract_words_and_formulas(pdf_bytes: bytes) -> str:
    """
    Extract only natural language words and mathematical formulas from a PDF.
    Ignores page numbers, headers, footers, tables, and other non‑content.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_content = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Get text blocks with layout info (position, font, etc.)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue  # Skip images/diagrams

            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    # Skip page numbers (short numbers near top/bottom)
                    if text.isdigit() and len(text) <= 4:
                        bbox = span["bbox"]
                        page_height = page.rect.height
                        if bbox[1] < 50 or bbox[3] > page_height - 50:
                            continue

                    # Check if the span contains math
                    is_math = False
                    if any(ch in text for ch in MATH_SYMBOLS):
                        is_math = True
                    elif MATH_REGEX.search(text):
                        is_math = True
                    # Heuristic: math often uses italic fonts
                    elif "italic" in span.get("font", "").lower():
                        is_math = True

                    if is_math:
                        # Keep the entire span as math
                        line_text += text + " "
                    else:
                        # Extract only words (letters, apostrophes, hyphens)
                        words = re.findall(r"[a-zA-Z']+(?:-[a-zA-Z]+)*", text)
                        if words:
                            line_text += " ".join(words) + " "

                # Skip very short lines that are likely headers
                if line_text.strip() and len(line_text.split()) > 3:
                    all_content.append(line_text.strip())

    # Join all lines and clean up extra spaces
    raw_text = " ".join(all_content)
    cleaned = re.sub(r'\s+', ' ', raw_text).strip()
    return cleaned

# ==========================================
# AI SUMMARIZATION
# ==========================================
def summarize_text(content: str) -> SummaryResponse:
    """Generate a summary using the loaded model."""
    inputs = tokenizer(content, return_tensors="pt", max_length=1024, truncation=True)
    input_len = inputs["input_ids"].shape[1]

    # Dynamic limits: summary length between 30% and 60% of input, capped at 512
    min_len = max(100, int(input_len * 0.3))
    max_len = min(512, int(input_len * 0.6))

    summary_ids = model.generate(
        inputs["input_ids"],
        min_length=min_len,
        max_length=max_len,
        length_penalty=2.5,
        num_beams=5,
        no_repeat_ngram_size=3,
        early_stopping=True
    )

    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    # Ensure we stop at a sentence boundary
    match = re.search(r'^(.*[.!?])', summary)
    if match:
        summary = match.group(1)

    word_count = len(summary.split())
    return SummaryResponse(summary=summary, wordCount=word_count)

# ==========================================
# ENDPOINTS
# ==========================================
@app.post("/generate-from-text", response_model=SummaryResponse)
async def generate_from_text(data: TextInput):
    """Summarize plain text input."""
    cleaned = re.sub(r'\s+', ' ', data.text).strip()
    return summarize_text(cleaned)

@app.post("/generate-from-pdf", response_model=SummaryResponse)
async def generate_from_pdf(file: UploadFile = File(...)):
    """Extract text and formulas from a PDF, then summarize."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    try:
        contents = await file.read()
        extracted = extract_words_and_formulas(contents)
        if not extracted:
            raise HTTPException(400, "No usable text or formulas found in PDF.")
        return summarize_text(extracted)
    except Exception as e:
        raise HTTPException(500, f"Error processing PDF: {str(e)}")

@app.post("/extract-pdf", response_model=ExtractResponse)
async def extract_pdf_only(file: UploadFile = File(...)):
    """Extract only words and formulas from a PDF (no summary)."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    try:
        contents = await file.read()
        extracted = extract_words_and_formulas(contents)
        if not extracted:
            raise HTTPException(400, "No usable text or formulas found in PDF.")
        word_count = len(extracted.split())
        return ExtractResponse(text=extracted, wordCount=word_count)
    except Exception as e:
        raise HTTPException(500, f"Error extracting PDF: {str(e)}")