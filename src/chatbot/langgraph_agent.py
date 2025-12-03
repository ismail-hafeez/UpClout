"""
LangGraph integration example for ChromaDB-powered chatbot.
Demonstrates agentic workflow with state management.
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from config.vertex_config import vector_store, llm, instruction


# Define the state structure
class AgentState(TypedDict):
    """State for the chatbot agent."""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    context: Annotated[str, "Retrieved context from ChromaDB"]
    query: Annotated[str, "Current user query"]


def retrieve_context(state: AgentState) -> AgentState:
    """
    Retrieve relevant context from ChromaDB based on user query.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with retrieved context
    """
    query = state["query"]
    
    # Perform similarity search
    docs = vector_store.similarity_search(query, k=5)
    
    # Combine retrieved documents into context
    context = "\n\n".join([
        f"Document {i+1}:\n{doc.page_content}\nMetadata: {doc.metadata}"
        for i, doc in enumerate(docs)
    ])
    
    state["context"] = context
    return state


def generate_response(state: AgentState) -> AgentState:
    """
    Generate AI response using retrieved context and LLM.
    
    Args:
        state: Current agent state with context
        
    Returns:
        Updated state with AI response
    """
    context = state["context"]
    query = state["query"]
    
    # Create prompt with context
    prompt = f"""
{instruction}

Context from database:
{context}

User Question: {query}

Answer:
"""
    
    # Generate response using Gemini 2.5 Flash
    response = llm.invoke(prompt)
    
    # Add AI message to conversation
    ai_message = AIMessage(content=response)
    state["messages"].append(ai_message)
    
    return state


def should_continue(state: AgentState) -> str:
    """
    Determine if the conversation should continue.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name or END
    """
    # Simple logic: end after generating response
    # You can extend this with more complex routing logic
    return END


def create_chatbot_graph():
    """
    Create a LangGraph workflow for the ChromaDB-powered chatbot.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)
    
    # Define edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_conditional_edges(
        "generate",
        should_continue,
        {END: END}
    )
    
    # Compile the graph
    app = workflow.compile()
    
    return app


def chat(query: str, conversation_history: list = None) -> dict:
    """
    Main chat function using LangGraph workflow.
    
    Args:
        query: User's question
        conversation_history: Previous messages in the conversation
        
    Returns:
        Response dictionary with answer and updated state
    """
    if conversation_history is None:
        conversation_history = []
    
    # Add user message to history
    user_message = HumanMessage(content=query)
    conversation_history.append(user_message)
    
    # Initialize state
    initial_state = {
        "messages": conversation_history,
        "context": "",
        "query": query
    }
    
    # Create and run the graph
    app = create_chatbot_graph()
    final_state = app.invoke(initial_state)
    
    # Extract the AI response
    ai_response = final_state["messages"][-1].content
    
    return {
        "answer": ai_response,
        "context": final_state["context"],
        "conversation_history": final_state["messages"]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph ChromaDB Chatbot Example")
    print("=" * 60)
    
    # Example conversation
    conversation = []
    
    # First query
    query1 = "Who are the top influencers in the fitness category?"
    print(f"\nUser: {query1}")
    
    response1 = chat(query1, conversation)
    print(f"\nOwly: {response1['answer']}")
    conversation = response1['conversation_history']
    
    # Follow-up query (with conversation context)
    query2 = "What are their engagement rates?"
    print(f"\n\nUser: {query2}")
    
    response2 = chat(query2, conversation)
    print(f"\nOwly: {response2['answer']}")
    
    print("\n" + "=" * 60)
    print(f"Total messages in conversation: {len(response2['conversation_history'])}")
    print("=" * 60)
