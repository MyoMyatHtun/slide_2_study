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
# Regex for URLs and links
URL_PATTERN = r'https?://\S+|www\.\S+'
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
    Cleans out page numbers, headers, and reference URLs (https/www).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_content = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    # 1. Skip page numbers (position-based heuristic)
                    if text.isdigit() and len(text) <= 4:
                        bbox = span["bbox"]
                        if bbox[1] < 50 or bbox[3] > page.rect.height - 50:
                            continue

                    # 2. Identify Math (symbols, regex patterns, or italics)
                    is_math = (any(ch in text for ch in MATH_SYMBOLS) or 
                               MATH_REGEX.search(text) or 
                               "italic" in span.get("font", "").lower())

                    if is_math:
                        line_text += text + " "
                    else:
                        # 3. Extract regular words only
                        words = re.findall(r"[a-zA-Z']+(?:-[a-zA-Z]+)*", text)
                        if words:
                            line_text += " ".join(words) + " "

                # 4. Filter out very short lines (likely headers/noise)
                if line_text.strip() and len(line_text.split()) > 3:
                    all_content.append(line_text.strip())

    # 5. Final Cleaning: Join, Remove URLs, and Fix Whitespace
    full_text = " ".join(all_content)
    full_text = re.sub(URL_PATTERN, '', full_text) # Strip https/www links
    cleaned = re.sub(r'\s+', ' ', full_text).strip()
    
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
    
from tokenizer import whitespace_tokenize, split_punctuation, analyze_and_export

@app.post("/extract-pdf")
async def extract_pdf_only(file: UploadFile = File(...)):
    contents = await file.read()
    text = extract_words_and_formulas(contents)
    
    # 1. Process tokens
    tokens = whitespace_tokenize(text)
    tokens = split_punctuation(tokens)
    
    # 2. Generate visualization data
    viz_data = analyze_and_export(tokens, file.filename)
    
    # 3. Send both the text AND the visualization stats to React
    return {
        "text": text,
        "wordCount": viz_data["total_tokens"],
        "visualization": viz_data # React can now use viz_data.top_tokens for charts
    }