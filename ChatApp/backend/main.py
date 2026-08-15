import os
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from rag import retrieve

load_dotenv()
app = FastAPI(title="Chat API")
@app.get("/health")
def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    reply: str
    image_url: Optional[str] = None

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages array is required")
    try:
        last_message = request.messages[-1].content

        # RAG retrieval
        retrieved_chunks, retrieved_images = retrieve(last_message, top_k=3)
        
        raw_context = "\n\n---\n\n".join(retrieved_chunks) if retrieved_chunks else ""
        candidate_image_url = next((img for img in retrieved_images if img), None)

        # Dual-step Gemini intent check
        relevance_prompt = (
            f"User Question: {last_message}\n\n"
            f"Retrieved Document Context:\n{raw_context}\n\n"
            "Task: Does this user question specifically require our internal document to answer it accurately, "
            "or is it a general knowledge question (science, English, history, psychology, etc.) that can be answered from general knowledge? "
            "Reply with ONLY one word: INTERNAL (if it requires our document) or GENERAL (if it's general knowledge or unrelated)."
        )
        
        eval_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=relevance_prompt
        )
        
        is_internal_file_query = "INTERNAL" in eval_response.text.upper()

        if is_internal_file_query and raw_context:
            context = raw_context
            best_image_url = candidate_image_url
        else:
            context = "No specific document context found."
            best_image_url = None

        system_instruction = (
            "You are a helpful assistant. Use the reference material below if it is relevant to answer the user's question. "
            "If the reference material does not contain the answer, rely on your own general knowledge to answer accurately. "
            "Do NOT draw ASCII text diagrams or text art; the system will automatically display the actual image file provided if available.\n\n"
            f"Reference Material:\n{context}"
        )

        history = []
        for m in request.messages[:-1]:
            role = "model" if m.role == "assistant" else "user"
            history.append({"role": role, "parts": [{"text": m.content}]})

        chat_session = client.chats.create(
            model="gemini-3.6-flash",
            history=history,
        )

        prompt = f"{system_instruction}\n\nUser Question: {last_message}"
        response = chat_session.send_message(prompt)

        return ChatResponse(reply=response.text, image_url=best_image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)