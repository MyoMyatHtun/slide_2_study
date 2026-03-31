from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz  # PyMuPDF
import re
import os
import json
import time
import urllib.error
import urllib.request
from typing import Any, Optional

try:
    from .tokenizer import whitespace_tokenize, split_punctuation, analyze_and_export
except ImportError:
    from tokenizer import whitespace_tokenize, split_punctuation, analyze_and_export
 

app = FastAPI()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "modelProvider": "huggingface",
        "modelId": HF_MODEL_ID,
        "tokenConfigured": bool(HF_TOKEN),
    }

# CORS for React frontend (adjust origin if needed)
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# HUGGING FACE INFERENCE CONFIGURATION
# ==========================================
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "dxskywalker/s2s_summarizer")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = os.getenv("HF_API_URL", f"https://api-inference.huggingface.co/models/{HF_MODEL_ID}")
HF_TIMEOUT_SECONDS = int(os.getenv("HF_TIMEOUT_SECONDS", "90"))

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
    visualization: Optional[dict[str, Any]] = None

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
    """Generate a summary through the Hugging Face Inference API."""
    if not HF_TOKEN:
        raise HTTPException(503, "HF_TOKEN is missing. Set Railway environment variable HF_TOKEN.")

    prompt_words = len(content.split())
    min_len = max(60, int(prompt_words * 0.25))
    max_len = min(350, max(min_len + 20, int(prompt_words * 0.55)))

    payload = {
        "inputs": content,
        "parameters": {
            "min_length": min_len,
            "max_length": max_len,
            "num_beams": 4,
            "do_sample": False,
            "repetition_penalty": 1.2,
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,
            "use_cache": True,
        },
    }

    req = urllib.request.Request(
        HF_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=HF_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(502, f"Hugging Face API error ({exc.code}): {detail[:300]}")
    except urllib.error.URLError as exc:
        raise HTTPException(503, f"Cannot reach Hugging Face API: {exc.reason}")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected inference error: {exc}")

    elapsed_ms = int((time.time() - start) * 1000)
    print(f"HF inference completed in {elapsed_ms} ms")

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(502, "Invalid JSON response from Hugging Face API")

    if isinstance(parsed, dict) and parsed.get("error"):
        error_text = str(parsed.get("error"))
        if "currently loading" in error_text.lower():
            raise HTTPException(503, "Model is warming up on Hugging Face. Retry in a few seconds.")
        raise HTTPException(502, f"Hugging Face returned an error: {error_text}")

    summary = ""
    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        if isinstance(first, dict):
            summary = first.get("summary_text") or first.get("generated_text") or ""
    elif isinstance(parsed, dict):
        summary = parsed.get("summary_text") or parsed.get("generated_text") or ""

    summary = re.sub(r'\s+', ' ', summary).strip()
    if not summary:
        raise HTTPException(502, "No summary_text returned by Hugging Face API")

    match = re.search(r'^(.*[.!?])', summary)
    if match:
        summary = match.group(1)

    return SummaryResponse(summary=summary, wordCount=len(summary.split()))

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
    """Extract words/formulas from a PDF and return token visualization metadata."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    try:
        contents = await file.read()
        text = extract_words_and_formulas(contents)
        if not text:
            raise HTTPException(400, "No usable text or formulas found in PDF.")

        tokens = whitespace_tokenize(text)
        tokens = split_punctuation(tokens)
        viz_data = analyze_and_export(tokens, file.filename)

        return ExtractResponse(
            text=text,
            wordCount=viz_data["total_tokens"],
            visualization=viz_data,
        )
    except Exception as e:
        raise HTTPException(500, f"Error extracting PDF: {str(e)}")