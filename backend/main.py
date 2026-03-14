from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import io
import fitz  # PyMuPDF
import re    # Python's built-in tool for cleaning text
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer # NEW IMPORTS

app = FastAPI()

# Allow React (running on port 5173) to talk to this Python Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# LOAD NLP MODEL ON STARTUP
# ==========================================
MODEL_PATH = "./model" # Make sure this matches your folder name!

print("Loading Slide 2 Study AI Model... (This will take a few moments)")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
    print("AI Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Make sure your model files are inside the 'model' directory.")

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
# ACTUAL AI LOGIC
# ==========================================
def process_content_with_ai(content: str) -> SummaryResponse:
    # 1. Tokenize the incoming cleaned text
    # max_length=1024 is the reading limit for BART
    inputs = tokenizer(content, return_tensors="pt", max_length=1024, truncation=True)
    
    # 2. CALCULATE DYNAMIC LIMITS
    # We force the summary to be at least 30% of the input's length.
    input_token_count = inputs["input_ids"].shape[1]
    
    # calc_min ensures a 700-word PDF (approx 930 tokens) gets at least 280 tokens (~210 words)
    calc_min = max(100, int(input_token_count * 0.3)) 
    calc_max = min(512, int(input_token_count * 0.6))

    # 3. Generate with "Length Persistence"
    summary_ids = model.generate(
        inputs["input_ids"], 
        min_length=calc_min,    # FORCES the AI to keep writing
        max_length=calc_max,    # Gives it room to include details
        length_penalty=2.5,     # Rewards longer, more detailed sentences
        num_beams=5,            # Better quality search
        no_repeat_ngram_size=3, # Prevents repetitive phrases
        early_stopping=True     # Allows a clean stop at a period (.)
    )
    
    # 4. Decode the output
    generated_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    # 5. SAFETY CLEANUP: Cut off any fragments after the last period
    import re
    match = re.search(r'^(.*[.!?])', generated_text)
    if match:
        generated_text = match.group(1)

    # 6. Count the words for the UI
    word_count = len(generated_text.split())
    
    return SummaryResponse(
        summary=generated_text,
        wordCount=word_count
    )
# ==========================================
# ENDPOINTS
# ==========================================
@app.post("/generate-from-text", response_model=SummaryResponse)
async def generate_text(data: TextInput):
    cleaned_text = re.sub(r'\s+', ' ', data.text).strip()
    return process_content_with_ai(cleaned_text)

@app.post("/generate-from-pdf", response_model=SummaryResponse)
async def generate_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        contents = await file.read()
        pdf_document = fitz.open(stream=contents, filetype="pdf")
        
        raw_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            raw_text += page.get_text() + " "
            
        cleaned_text = re.sub(r'\s+', ' ', raw_text)
        cleaned_text = re.sub(r'(?<=\b[a-zA-Z])\s(?=[a-zA-Z]\b)', '', cleaned_text).strip()
        
        print(f"\nExtracted {len(cleaned_text.split())} words from {file.filename}")

        if not cleaned_text:
            raise HTTPException(status_code=400, detail="Could not extract text from this PDF.")

        return process_content_with_ai(cleaned_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/extract-pdf", response_model=ExtractResponse)
async def extract_pdf_only(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        contents = await file.read()
        pdf_document = fitz.open(stream=contents, filetype="pdf")
        
        raw_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            raw_text += page.get_text() + " "
            
        cleaned_text = re.sub(r'\s+', ' ', raw_text)
        cleaned_text = re.sub(r'(?<=\b[a-zA-Z])\s(?=[a-zA-Z]\b)', '', cleaned_text).strip()

        if not cleaned_text:
            raise HTTPException(status_code=400, detail="No text found.")

        word_count = len(cleaned_text.split())
        return ExtractResponse(text=cleaned_text, wordCount=word_count)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting PDF: {str(e)}")