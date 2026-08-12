# build_index.py
import os
import json
import numpy as np
import fitz  # PyMuPDF
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PDF_PATH = "Cell_Organelles_Guide.pdf"
INDEX_PATH = "rag_index.json"
EMBED_MODEL = "gemini-embedding-2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

def extract_pages_with_images(pdf_path: str):
    doc = fitz.open(pdf_path)
    page_data = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text() or ""
        
        # Look for images extracted for this page
        image_dir = "../frontend/public/organelle_images"
        matching_images = [
            f"/organelle_images/{img}" for img in os.listdir(image_dir) 
            if img.startswith(f"organelle_{page_num}_")
        ]
        image_url = matching_images[0] if matching_images else None
        
        page_data.append({"text": text, "image_url": image_url})
        
    return page_data

def chunk_text_with_images(pages_data, size: int, overlap: int):
    chunk_records = []
    
    for page in pages_data:
        text = page["text"]
        image_url = page["image_url"]
        
        start = 0
        while start < len(text):
            end = start + size
            chunk = text[start:end].strip()
            if chunk:
                chunk_records.append({
                    "chunk": chunk,
                    "image_url": image_url
                })
            start += size - overlap
            
    return chunk_records

def embed_chunks(records: list[dict]) -> list[list[float]]:
    vectors = []
    for i, rec in enumerate(records):
        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=rec["chunk"],
        )
        vectors.append(result.embeddings[0].values)
        print(f"embedded chunk {i+1}/{len(records)}")
    return vectors

def main():
    pages_data = extract_pages_with_images(PDF_PATH)
    chunk_records = chunk_text_with_images(pages_data, CHUNK_SIZE, CHUNK_OVERLAP)
    
    chunks = [r["chunk"] for r in chunk_records]
    image_urls = [r["image_url"] for r in chunk_records]
    
    vectors = embed_chunks(chunk_records)

    data = {
        "chunks": chunks, 
        "image_urls": image_urls,
        "vectors": vectors
    }
    with open(INDEX_PATH, "w") as f:
        json.dump(data, f)

    print(f"Indexed {len(chunks)} chunks with images into {INDEX_PATH}")

if __name__ == "__main__":
    main()