from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, MessagesState, START
from langgraph.checkpoint.memory import MemorySaver
import os
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import StreamingResponse

# File import - CHANGED TO GROQ CONFIG
from src.chatbot.config.groq_config import llm, instruction, vector_store

def call_model(state: MessagesState):
    """LangGraph node for RAG processing with Groq."""
    user_input = state['messages'][-1].content
    history = state.get("history", [])

    results = vector_store.similarity_search(user_input, k=5)

    context = ""
    for idx, doc in enumerate(results, 1):
        username = doc.metadata.get("username", f"Profile {idx}")
        context += f"[@{username}]: {doc.page_content}\n"

    history_lines = []
    for m in state["messages"]:
        if hasattr(m, "content"):
            role = "User" if m.type == "human" else "Bot"
            history_lines.append(f"{role}: {m.content}")

    prompt = (
        f"{instruction}\n\n"
        f"Conversation so far:\n"
        + "\n".join(history_lines)
        + f"\n\nContext from Database:\n{context}\n\nUser question: {user_input}\n\nAnswer:"
    )

    response = llm.invoke(prompt)
    # Extract content from Groq response (AIMessage)
    answer = response.content if hasattr(response, 'content') else str(response)
    
    history.append({"question": user_input, "answer": answer})
    state["messages"].append(AIMessage(content=answer))
    
    return {
        "messages": state["messages"],
        "history": history,
        "answer": answer
    }

# LangGraph Setup
graph = StateGraph(MessagesState)
graph.add_node("RAG", call_model)
graph.add_edge(START, "RAG")
graph.add_edge("RAG", END)
memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)

# FastAPI App
app = FastAPI(title="UpClout Groq Chatbot")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str
    history: list 
    thread_id: Optional[str] = None

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Streaming chat endpoint for the Groq backend."""
    thread_id = req.thread_id or str(uuid.uuid4())
    
    # 1. RAG Retrieval
    user_input = req.message
    results = vector_store.similarity_search(user_input, k=5)
    context = ""
    for idx, doc in enumerate(results, 1):
        username = doc.metadata.get("username", f"Profile {idx}")
        context += f"[@{username}]: {doc.page_content}\n"

    # 2. Build Prompt
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

    # 3. Streaming Generator
    async def generate():
        # Groq streaming via ChatGroq.stream
        for chunk in llm.stream(prompt):
             content = chunk.content if hasattr(chunk, "content") else str(chunk)
             yield content
    
    return StreamingResponse(generate(), media_type="text/plain", headers={"X-Thread-ID": thread_id})
