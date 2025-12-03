"""
Query ChromaDB using LangChain for semantic search with Gemini 2.5 Flash.
Includes specialized functions for influencer discovery and filtering.
"""

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional
from config.vertex_config import vector_store, llm, instruction


def create_rag_chain(retriever_k: int = 5):
    """
    Create a RAG (Retrieval-Augmented Generation) chain using LangChain.
    
    Args:
        retriever_k: Number of documents to retrieve for context
        
    Returns:
        RetrievalQA chain
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
    
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # Create RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    return qa_chain


def query_chromadb(question: str, k: int = 5) -> dict:
    """
    Query ChromaDB and get AI-generated response.
    
    Args:
        question: User's question
        k: Number of relevant documents to retrieve
        
    Returns:
        Dictionary with 'result' and 'source_documents'
    """
    qa_chain = create_rag_chain(retriever_k=k)
    response = qa_chain.invoke({"query": question})
    return response


def similarity_search(query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Document]:
    """
    Perform direct similarity search without LLM generation.
    
    Args:
        query: Search query
        k: Number of results to return
        filter_dict: Optional metadata filters
        
    Returns:
        List of relevant documents
    """
    if filter_dict:
        results = vector_store.similarity_search(query, k=k, filter=filter_dict)
    else:
        results = vector_store.similarity_search(query, k=k)
    return results


def similarity_search_with_score(query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[tuple]:
    """
    Perform similarity search with relevance scores.
    
    Args:
        query: Search query
        k: Number of results to return
        filter_dict: Optional metadata filters
        
    Returns:
        List of tuples (document, score)
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
    """
    Search influencers within a specific follower range.
    
    Args:
        query: Search query (e.g., "fitness influencers")
        min_followers: Minimum follower count
        max_followers: Maximum follower count
        k: Number of results
        
    Returns:
        List of matching influencer documents
    """
    # Note: ChromaDB filter syntax may vary, adjust as needed
    filter_dict = {
        "$and": [
            {"followers": {"$gte": min_followers}},
            {"followers": {"$lte": max_followers}}
        ]
    }
    
    return similarity_search(query, k=k, filter_dict=filter_dict)


def search_by_engagement(query: str, min_engagement: float = 0.0, k: int = 5) -> List[Document]:
    """
    Search influencers with minimum engagement rate.
    
    Args:
        query: Search query
        min_engagement: Minimum engagement rate (e.g., 3.0 for 3%)
        k: Number of results
        
    Returns:
        List of matching influencer documents
    """
    filter_dict = {
        "engagement_rate": {"$gte": min_engagement}
    }
    
    return similarity_search(query, k=k, filter_dict=filter_dict)


def search_by_location(location: str, query: str = "", k: int = 5) -> List[Document]:
    """
    Search influencers by location.
    
    Args:
        location: Location to filter by
        query: Optional additional search query
        k: Number of results
        
    Returns:
        List of matching influencer documents
    """
    search_query = f"{query} {location}" if query else location
    
    filter_dict = {
        "location": {"$eq": location}
    }
    
    return similarity_search(search_query, k=k, filter_dict=filter_dict)


def search_by_category(category: str, query: str = "", k: int = 5) -> List[Document]:
    """
    Search influencers by business category/niche.
    
    Args:
        category: Business category (e.g., "Fashion", "Beauty", "Fitness")
        query: Optional additional search query
        k: Number of results
        
    Returns:
        List of matching influencer documents
    """
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
    """
    Find rising star influencers: high engagement with moderate follower count.
    
    Args:
        query: Search query
        min_engagement: Minimum engagement rate (default 3%)
        min_followers: Minimum followers (default 10K)
        max_followers: Maximum followers (default 100K)
        k: Number of results
        
    Returns:
        List of rising star influencer documents
    """
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
    """
    Find top-tier influencers: high followers and good engagement.
    
    Args:
        query: Search query
        min_followers: Minimum followers (default 100K)
        min_engagement: Minimum engagement rate (default 2%)
        k: Number of results
        
    Returns:
        List of top influencer documents
    """
    filter_dict = {
        "$and": [
            {"followers": {"$gte": min_followers}},
            {"engagement_rate": {"$gte": min_engagement}}
        ]
    }
    
    return similarity_search(query, k=k, filter_dict=filter_dict)


def find_verified_influencers(query: str = "", k: int = 5) -> List[Document]:
    """
    Search for verified influencers only.
    
    Args:
        query: Search query
        k: Number of results
        
    Returns:
        List of verified influencer documents
    """
    filter_dict = {
        "is_verified": {"$eq": True}
    }
    
    return similarity_search(query, k=k, filter_dict=filter_dict)


def search_by_hashtags(hashtags: List[str], query: str = "", k: int = 5) -> List[Document]:
    """
    Search influencers who frequently use specific hashtags.
    
    Args:
        hashtags: List of hashtags to search for (without #)
        query: Optional additional search query
        k: Number of results
        
    Returns:
        List of matching influencer documents
    """
    # Combine hashtags with query
    hashtag_query = " ".join([f"#{tag}" for tag in hashtags])
    search_query = f"{query} {hashtag_query}" if query else hashtag_query
    
    # Note: This searches semantically; for exact hashtag matching,
    # you'd need to filter by the top_hashtags metadata field
    return similarity_search(search_query, k=k)


def get_influencer_summary(username: str) -> Optional[Dict[str, Any]]:
    """
    Get a comprehensive summary of a specific influencer.
    
    Args:
        username: Influencer username (with or without @)
        
    Returns:
        Dictionary with influencer data or None if not found
    """
    # Remove @ if present
    username = username.lstrip('@')
    
    # Search for the specific influencer
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


def compare_influencers(usernames: List[str]) -> List[Dict[str, Any]]:
    """
    Compare multiple influencers side by side.
    
    Args:
        usernames: List of influencer usernames
        
    Returns:
        List of influencer summaries
    """
    results = []
    
    for username in usernames:
        summary = get_influencer_summary(username)
        if summary:
            results.append(summary)
    
    return results


# ============================================================================
# Helper Functions
# ============================================================================

def print_search_results(results: List[Document], show_metadata: bool = True):
    """
    Pretty print search results.
    
    Args:
        results: List of Document objects
        show_metadata: Whether to show metadata
    """
    print(f"\nFound {len(results)} results:\n")
    print("=" * 80)
    
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. @{doc.metadata.get('username', 'Unknown')}")
        print(f"   Name: {doc.metadata.get('name', 'N/A')}")
        print(f"   Followers: {doc.metadata.get('followers', 0):,}")
        print(f"   Engagement: {doc.metadata.get('engagement_rate', 0):.2f}%")
        print(f"   Category: {doc.metadata.get('category', 'N/A')}")
        print(f"   Location: {doc.metadata.get('location', 'N/A')}")
        
        if show_metadata and doc.metadata.get('top_hashtags'):
            hashtags = ", ".join([f"#{tag}" for tag in doc.metadata['top_hashtags']])
            print(f"   Top Hashtags: {hashtags}")
        
        print(f"\n   Preview: {doc.page_content[:200]}...")
        print("-" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("ChromaDB Query Examples - Influencer Search")
    print("=" * 80)
    
    # Example 1: Basic semantic search
    print("\n1. Basic Search: Fitness Influencers")
    results = similarity_search("fitness workout gym", k=3)
    print_search_results(results)
    
    # Example 2: Rising stars
    print("\n2. Finding Rising Stars (High Engagement, 10K-100K followers)")
    rising = find_rising_stars(query="fashion beauty", min_engagement=3.0, k=3)
    print_search_results(rising)
    
    # Example 3: Top influencers
    print("\n3. Top Influencers (100K+ followers)")
    top = find_top_influencers(query="lifestyle", min_followers=100000, k=3)
    print_search_results(top)
    
    # Example 4: RAG with LLM
    print("\n4. RAG Query with Gemini 2.5 Flash")
    question = "Who are the best fitness influencers with high engagement?"
    response = query_chromadb(question, k=3)
    print(f"\nQuestion: {question}")
    print(f"\nAnswer: {response['result']}")
    print(f"\nSources: {len(response['source_documents'])} influencers analyzed")
    
    print("\n" + "=" * 80)
