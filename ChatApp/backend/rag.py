# rag.py - AWS Lambda + S3 Ready
import os
import json
import numpy as np
import boto3
from dotenv import load_dotenv
from google import genai

# 1. AWS S3 Config - Hardcoded for Lambda
BUCKET_NAME = "rag-bot-data-urwa" # <-- IMPORTANT: apna bucket name yahan likho
AWS_REGION = "ap-south-1" # <-- apna region yahan likho
s3 = boto3.client('s3', region_name=AWS_REGION)

# 2. Local vs Lambda Path
INDEX_PATH = "/tmp/rag_index.json" # Lambda mein sirf /tmp writable hota hai
LOCAL_INDEX_PATH = "rag_index.json" # Local testing ke liye

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
EMBED_MODEL = "gemini-embedding-2"

_chunks: list[str] = []
_image_urls: list[str] = []
_vectors: np.ndarray | None = None

def _load_index():
    global _chunks, _image_urls, _vectors
    if _vectors is not None:
        return

    # Try to download from S3 first. If fail, use local file for testing
    try:
        s3.download_file(BUCKET_NAME, "rag_index.json", INDEX_PATH)
        path_to_use = INDEX_PATH
        print("Loaded rag_index.json from S3")
    except Exception as e:
        print(f"Warning: Could not download from S3. Error: {e}")
        print("Falling back to local rag_index.json")
        path_to_use = LOCAL_INDEX_PATH

    with open(path_to_use, "r") as f:
        data = json.load(f)

    _chunks = data["chunks"]
    _image_urls = data.get("image_urls", [])
    _vectors = np.array(data["vectors"], dtype=np.float32)
    _vectors = _vectors / np.linalg.norm(_vectors, axis=1, keepdims=True)

def retrieve(query: str, top_k: int = 3) -> tuple[list[str], list[str]]:
    _load_index()
    if _vectors is None:
        return ["Error: Index not loaded"], []

    result = client.models.embed_content(model=EMBED_MODEL, contents=query)
    q_vec = np.array(result.embeddings[0].values, dtype=np.float32)
    q_vec = q_vec / np.linalg.norm(q_vec)
    scores = _vectors @ q_vec
    top_idx = np.argsort(scores)[::-1][:top_k]
    retrieved_chunks = [_chunks[i] for i in top_idx]
    retrieved_images = [_image_urls[i] if i < len(_image_urls) else None for i in top_idx]
    return retrieved_chunks, retrieved_images