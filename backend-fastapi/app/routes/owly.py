import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

# AI logic import 
from app.chatbot import llm, instruction, vector_store

router = APIRouter(prefix="/api/owly", tags=["owly"])

class ChatRequest(BaseModel):
    message: str
    history: list 
    thread_id: Optional[str] = None

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Streaming chat endpoint for the Owly assistant."""
    thread_id = req.thread_id or str(uuid.uuid4())
    
    # 1. RAG Retrieval from ChromaDB
    user_input = req.message
    results = vector_store.similarity_search(user_input, k=5)
    
    context = ""
    for idx, doc in enumerate(results, 1):
        username = doc.metadata.get("username", f"Profile {idx}")
        context += f"[@{username}]: {doc.page_content}\n"

    # 2. Build Prompt including history
    # Frontend sends history as [{"role": "user/bot", "content": "..."}]
    history_lines = []
    for m in req.history:
        role = "User" if m["role"] == "user" else "Bot"
        history_lines.append(f"{role}: {m['content']}")

    prompt = (
        f"{instruction}\n\n"
        f"Conversation so far:\n"
        + "\n".join(history_lines)
        + f"\n\nContext from Database:\n{context}\n\nUser question: {user_input}\n\nAnswer:"
    )

    # 3. Streaming Response
    async def generate():
        # Groq streaming
        for chunk in llm.stream(prompt):
             content = chunk.content if hasattr(chunk, "content") else str(chunk)
             yield content
    
    return StreamingResponse(
        generate(), 
        media_type="text/plain", 
        headers={"X-Thread-ID": thread_id}
    )
