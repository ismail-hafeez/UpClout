"""
Query ChromaDB using LangChain for semantic search with Groq Llama 3.
Includes specialized functions for influencer discovery and filtering.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, Optional

# File import - CHANGED TO GROQ CONFIG
from src.chatbot.config.groq_config import vector_store, llm, instruction


def format_docs(docs):
    """Format documents for context."""
    return "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])


def create_rag_chain(retriever_k: int = 5):
    """
    Create a RAG (Retrieval-Augmented Generation) chain using LangChain LCEL.
    """
    # Create retriever from vector store
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": retriever_k}
    )
    
    # Create prompt template
    prompt_template = f"""
{instruction}

Context from database:
{{context}}

User Question: {{question}}

Answer:
"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # Create RAG chain using LCEL
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain, retriever


def query_chromadb(question: str, k: int = 5) -> dict:
    """
    Query ChromaDB and get AI-generated response.
    """
    rag_chain, retriever = create_rag_chain(retriever_k=k)
    
    # Get the answer
    result = rag_chain.invoke(question)
    
    # Get source documents
    source_documents = retriever.invoke(question)
    
    return {
        "result": result,
        "source_documents": source_documents
    }


def similarity_search(query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Document]:
    """
    Perform direct similarity search without LLM generation.
    """
    if filter_dict:
        results = vector_store.similarity_search(query, k=k, filter=filter_dict)
    else:
        results = vector_store.similarity_search(query, k=k)
    return results


def similarity_search_with_score(query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[tuple]:
    """
    Perform similarity search with relevance scores.
    """
    if filter_dict:
        results = vector_store.similarity_search_with_score(query, k=k, filter=filter_dict)
    else:
        results = vector_store.similarity_search_with_score(query, k=k)
    return results


# ============================================================================
# Specialized Search Functions for Influencers
# ============================================================================

def search_by_followers_range(query: str, min_followers: int = 0, max_followers: int = float('inf'), k: int = 5) -> List[Document]:
    """Search influencers within a specific follower range."""
    filter_dict = {
        "$and": [
            {"followers": {"$gte": min_followers}},
            {"followers": {"$lte": max_followers}}
        ]
    }
    return similarity_search(query, k=k, filter_dict=filter_dict)


def search_by_engagement(query: str, min_engagement: float = 0.0, k: int = 5) -> List[Document]:
    """Search influencers with minimum engagement rate."""
    filter_dict = {
        "engagement_rate": {"$gte": min_engagement}
    }
    return similarity_search(query, k=k, filter_dict=filter_dict)


def search_by_location(location: str, query: str = "", k: int = 5) -> List[Document]:
    """Search influencers by location."""
    search_query = f"{query} {location}" if query else location
    filter_dict = {
        "location": {"$eq": location}
    }
    return similarity_search(search_query, k=k, filter_dict=filter_dict)


def search_by_category(category: str, query: str = "", k: int = 5) -> List[Document]:
    """Search influencers by business category/niche."""
    search_query = f"{query} {category}" if query else category
    filter_dict = {
        "category": {"$eq": category}
    }
    return similarity_search(search_query, k=k, filter_dict=filter_dict)


def find_rising_stars(query: str = "rising influencers", 
                      min_engagement: float = 3.0,
                      min_followers: int = 10000,
                      max_followers: int = 100000,
                      k: int = 10) -> List[Document]:
    """Find rising stars: high engagement with moderate follower count."""
    filter_dict = {
        "$and": [
            {"engagement_rate": {"$gte": min_engagement}},
            {"followers": {"$gte": min_followers}},
            {"followers": {"$lte": max_followers}}
        ]
    }
    return similarity_search(query, k=k, filter_dict=filter_dict)


def find_top_influencers(query: str = "top influencers",
                        min_followers: int = 100000,
                        min_engagement: float = 2.0,
                        k: int = 10) -> List[Document]:
    """Find top-tier influencers: high followers and good engagement."""
    filter_dict = {
        "$and": [
            {"followers": {"$gte": min_followers}},
            {"engagement_rate": {"$gte": min_engagement}}
        ]
    }
    return similarity_search(query, k=k, filter_dict=filter_dict)


def find_verified_influencers(query: str = "", k: int = 5) -> List[Document]:
    """Search for verified influencers only."""
    filter_dict = {
        "is_verified": {"$eq": True}
    }
    return similarity_search(query, k=k, filter_dict=filter_dict)


def get_influencer_summary(username: str) -> Optional[Dict[str, Any]]:
    """Get a comprehensive summary of a specific influencer."""
    username = username.lstrip('@')
    results = similarity_search(f"@{username}", k=1)
    
    if not results:
        return None
    
    doc = results[0]
    return {
        "content": doc.page_content,
        "metadata": doc.metadata,
        "username": doc.metadata.get("username"),
        "name": doc.metadata.get("name"),
        "followers": doc.metadata.get("followers"),
        "engagement_rate": doc.metadata.get("engagement_rate"),
        "category": doc.metadata.get("category"),
        "location": doc.metadata.get("location"),
        "top_hashtags": doc.metadata.get("top_hashtags", [])
    }


def classify_intent(query: str) -> Dict[str, Any]:
    """Classify user intent using Groq LLM."""
    classification_prompt = f"""Analyze this user query and classify the intent. Extract relevant parameters.

User Query: "{query}"

Classify into ONE of these intents:
1. GENERAL_CHAT - General questions, RAG-based answers
2. RISING_STARS - Looking for rising influencers
3. TOP_INFLUENCERS - Looking for top-tier influencers
4. SPECIFIC_LOOKUP - Looking up a specific influencer
5. COMPARE - Comparing influencers
6. SIMILARITY_SEARCH - Finding similar influencers

Extract these parameters if mentioned:
- usernames: List of @usernames mentioned
- category/niche: Business category
- min_followers: Minimum follower count
- max_followers: Maximum follower count
- min_engagement: Minimum engagement rate percentage
- num_results: Number of results requested (default 5)
- location: Geographic location

Respond ONLY with valid JSON in this exact format:
{{
    "intent": "INTENT_TYPE",
    "parameters": {{
        "usernames": [],
        "category": "",
        "min_followers": null,
        "max_followers": null,
        "min_engagement": null,
        "num_results": 5,
        "location": ""
    }},
    "original_query": "the query"
}}"""
    
    try:
        response = llm.invoke(classification_prompt)
        # Handle both ChatResponse and string results (LLM typically returns BaseMessage)
        content = response.content if hasattr(response, 'content') else str(response)
        
        import json
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"intent": "GENERAL_CHAT", "parameters": {"num_results": 5}, "original_query": query}
    except Exception as e:
        print(f"⚠️ Intent classification error: {e}")
        return {"intent": "GENERAL_CHAT", "parameters": {"num_results": 5}, "original_query": query}


def route_query(query: str) -> str:
    """Route user query to appropriate function based on intent (Groq Version)."""
    classification = classify_intent(query)
    intent = classification.get("intent", "GENERAL_CHAT")
    params = classification.get("parameters", {})
    
    print(f"\n🤔 [Groq] Understanding your request... (Intent: {intent})")
    
    try:
        if intent == "SPECIFIC_LOOKUP":
            usernames = params.get("usernames", [])
            if not usernames: return "❌ Please specify an influencer username."
            summary = get_influencer_summary(usernames[0])
            
            if summary:
                resp = f"\n📊 Profile: @{summary['username']}\nFollowers: {summary['followers']:,}\nEngagement: {summary['engagement_rate']:.2f}%\n"
                resp += f"Bio:\n{summary['content']}\n"
                return resp
            return f"❌ Influencer not found."
        
        elif intent == "GENERAL_CHAT":
            num_results = params.get("num_results", 5)
            rag_response = query_chromadb(query, k=num_results)
            return f"\n🤖 Owly (Groq) Answer:\n\n{rag_response['result']}\n\n🔍 Analyzed {len(rag_response['source_documents'])} profiles."
        
        else:
            # Fallback for complex intents in this simplified script
            return query_chromadb(query, k=5)['result']
            
    except Exception as e:
        return f"❌ Error processing query: {str(e)}"


def interactive_query():
    """Interactive CLI for Groq-based chatbot."""
    print("=" * 80)
    print("🤖 UpClout Influencer Chatbot - GROQ MODE")
    print("=" * 80)
    while True:
        user_input = input("\n💬 You: ").strip()
        if not user_input or user_input.lower() in ["exit", "quit"]: break
        print(f"\n{route_query(user_input)}")


if __name__ == "__main__":
    interactive_query()
