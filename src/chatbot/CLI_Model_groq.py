from langgraph.graph import StateGraph, END, MessagesState, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import sys
import os

# Add parent directory to path for imports if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# File imports - CHANGED TO GROQ CONFIG
from src.chatbot.config.groq_config import vector_store, instruction, llm

def call_model(state: MessagesState):
    """LangGraph node for RAG processing with Groq."""
    user_input = state['messages'][-1].content
    history = state.get("history", [])

    # Similarity search
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

    # STREAMING RESPONSE
    response_content = ""
    print("\nAssistant (Groq):", end=" ", flush=True)
    
    # Groq streaming
    for chunk in llm.stream(prompt):
        part = getattr(chunk, "content", str(chunk))
        print(part, end="", flush=True)
        response_content += part
    print()  # Newline

    history.append({"question": user_input, "answer": response_content})
    state["messages"].append(AIMessage(content=response_content))
    
    return {
        "messages": state["messages"],
        "history": history,
        "answer": response_content
    }

# LangGraph Setup
graph = StateGraph(MessagesState)
graph.add_node("RAG", call_model)
graph.add_edge(START, "RAG")
graph.add_edge("RAG", END)

memory = MemorySaver()
THREAD_ID = str(uuid.uuid4())
config = {"configurable": {"thread_id": THREAD_ID}}
app = graph.compile(checkpointer=memory)

def run_model():
    """Interactive CLI runner for the Groq model."""
    print("=" * 80)
    print("🤖 UpClout Chatbot - GROQ CLI MODE")
    print("=" * 80)
    print("Type 'exit' to quit.\n")
    
    state = {
        "messages": [],
        "history": []
    }
    
    while True:
        user = input("User: ")
        if user.lower() in ['exit', 'quit']:
            break

        # Create user message
        user_msg = HumanMessage(content=user)
        state["messages"].append(user_msg)

        # Generate response (updates state)
        state = app.invoke(state, config)

if __name__ == "__main__":
    run_model()
