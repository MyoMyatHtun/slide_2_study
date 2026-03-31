# -*- coding: utf-8 -*-
import re
import json
import os
import tkinter as tk
from tkinter import filedialog
from collections import Counter

# ============================================================
# CONFIGURATION
# ============================================================
MAX_INPUT_CHARS = 50000
SUPPORTED_FORMATS = [('.Text files', '*.txt'), ('.PDF files', '*.pdf'), ('All files', '*.*')]

def whitespace_tokenize(text):
    """Splits text into basic chunks by whitespace."""
    return text.split()

def split_punctuation(tokens):
    """Separates punctuation from words for better visualization."""
    punctuation_marks = set(',.!?;:()[]{}"\'')
    new_tokens = []
    for token in tokens:
        if token and token[-1] in punctuation_marks and len(token) > 1:
            new_tokens.extend([token[:-1], token[-1]])
        elif token and token[0] in punctuation_marks and len(token) > 1:
            new_tokens.extend([token[0], token[1:]])
        else:
            new_tokens.append(token)
    return new_tokens

def analyze_and_export(tokens, filename):
    """
    Analyzes tokens and formats them for Frontend Visualization.
    Returns a dictionary ready for a React/API response.
    """
    counter = Counter(tokens)
    
    # Format top 10 for charts (e.g., Bar Charts)
    chart_data = [
        {"name": word, "value": count} 
        for word, count in counter.most_common(10)
    ]
    
    analysis = {
        "filename": filename,
        "total_tokens": len(tokens),
        "unique_tokens": len(set(tokens)),
        "top_tokens": chart_data,  # Direct data for frontend charts
        "vocabulary_density": round(len(set(tokens)) / len(tokens), 2) if tokens else 0,
        "token_preview": tokens[:50] # Show how it was split
    }
    
    # Local Save for record-keeping
    base_name = os.path.splitext(filename)[0]
    output_file = f"{base_name}_viz_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=4)
        
    print(f"✅ Visualization data ready for: {filename}")
    return analysis

def get_local_files():
    """GUI to select files when running the script directly."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    paths = filedialog.askopenfilenames(title="Select files", filetypes=SUPPORTED_FORMATS)
    
    results = {}
    for p in paths:
        with open(p, 'rb') as f:
            results[os.path.basename(p)] = f.read().decode('utf-8', errors='ignore')
    return results

if __name__ == "__main__":
    print("🚀 Running Tokenizer Visualization Tool...")
    files = get_local_files()
    for name, content in files.items():
        # Step-by-step processing
        t1 = whitespace_tokenize(content)
        t2 = split_punctuation(t1)
        # Export for frontend
        report = analyze_and_export(t2, name)
        print(f"Summary: {report['total_tokens']} tokens, {report['unique_tokens']} unique.")