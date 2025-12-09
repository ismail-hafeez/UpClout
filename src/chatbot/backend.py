from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, MessagesState, START
from langgraph.checkpoint.memory import MemorySaver
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
# file import
from config.vertex_config import llm, instruction, vector_store

def call_model(state: MessagesState):
    user_input = state['messages'][-1].content
    history = state.get("history", [])

    results = vector_store.similarity_search(user_input, k=5)

    context = ""
    for idx, doc in enumerate(results, 1):
        code = doc.metadata.get("code", f"Section {idx}")
        context += f"[{code}]: {doc.page_content}\n"

    history_lines = []
    for m in state["messages"]:
        if hasattr(m, "content"):
            role = "User" if m.type == "human" else "Bot"
            history_lines.append(f"{role}: {m.content}")

    prompt = (
        f"{instruction}\n\n"
        f"Conversation so far:\n"
        + "\n".join(history_lines)
        + f"\n\nContext:\n{context}\n\nUser question: {user_input}\n\nAnswer:"
    )

    response = llm.invoke(prompt)
    history.append({"question": user_input, "answer": response})
    state["messages"].append(AIMessage(content=response))
    return {
        "messages": state["messages"],
        "history": history,
        "answer": response
    }

# Set up LangGraph state machine
graph = StateGraph(MessagesState)
graph.add_node("RAG", call_model)
graph.add_edge(START, "RAG")
graph.add_edge("RAG", END)
memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)  

# --- FastAPI section ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

from typing import Optional

class ChatRequest(BaseModel):
    message: str
    history: list 
    thread_id: Optional[str] = None

from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    
    # 1. Prepare Retrieval Context
    user_input = req.message
    results = vector_store.similarity_search(user_input, k=5)
    context = ""
    for idx, doc in enumerate(results, 1):
        code = doc.metadata.get("code", f"Section {idx}")
        context += f"[{code}]: {doc.page_content}\n"

    # 2. Build Prompt from History
    # We use the history passed from frontend to construct the prompt conversation
    history_lines = []
    for m in req.history:
        role = "User" if m["role"] == "user" else "Bot"
        history_lines.append(f"{role}: {m['content']}")

    prompt = (
        f"{instruction}\n\n"
        f"Conversation so far:\n"
        + "\n".join(history_lines)
        + f"\n\nContext:\n{context}\n\nUser question: {user_input}\n\nAnswer:"
    )

    # 3. Generator Function
    async def generate():
        # Stream response
        for chunk in llm.stream(prompt):
             # VertexAI result chunk usually has .content
             content = chunk.content if hasattr(chunk, "content") else str(chunk)
             yield content
    
    # Return streaming response
    # We pass thread_id back as a header so frontend can persist it
    return StreamingResponse(generate(), media_type="text/plain", headers={"X-Thread-ID": thread_id})


