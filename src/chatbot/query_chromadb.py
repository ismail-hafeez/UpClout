"""
Query ChromaDB using LangChain for semantic search with Gemini 2.5 Flash.
Includes specialized functions for influencer discovery and filtering.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, Optional
from config.vertex_config import vector_store, llm, instruction


def format_docs(docs):
    """Format documents for context."""
    return "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])


def create_rag_chain(retriever_k: int = 5):
    """
    Create a RAG (Retrieval-Augmented Generation) chain using LangChain LCEL.
    
    Args:
        retriever_k: Number of documents to retrieve for context
        
    Returns:
        Runnable RAG chain
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
    
    Args:
        question: User's question
        k: Number of relevant documents to retrieve
        
    Returns:
        Dictionary with 'result' and 'source_documents'
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


def interactive_query():
    """
    Interactive query interface for the chatbot.
    Allows users to enter custom queries and choose search modes.
    """
    print("=" * 80)
    print("🤖 UpClout Influencer Chatbot - Interactive Mode")
    print("=" * 80)
    print("\nWelcome! Ask me anything about influencers in the database.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        print("\n" + "-" * 80)
        print("Choose a search mode:")
        print("  1. 💬 AI Chat (RAG with Gemini) - Ask natural language questions")
        print("  2. 🔍 Similarity Search - Find similar influencers")
        print("  3. ⭐ Rising Stars - High engagement, 10K-100K followers")
        print("  4. 🏆 Top Influencers - 100K+ followers")
        print("  5. 👤 Specific Influencer - Look up by username")
        print("  6. 📊 Compare Influencers - Compare multiple influencers")
        print("  0. ❌ Exit")
        print("-" * 80)
        
        mode = input("\nSelect mode (0-6): ").strip()
        
        if mode == "0" or mode.lower() in ["exit", "quit"]:
            print("\n👋 Thanks for using UpClout Chatbot! Goodbye!")
            break
        
        elif mode == "1":
            # AI Chat with RAG
            query = input("\n💬 Enter your question: ").strip()
            if not query or query.lower() in ["exit", "quit"]:
                continue
            
            k = input("Number of sources to analyze (default 5): ").strip()
            k = int(k) if k.isdigit() else 5
            
            print("\n🤔 Thinking...")
            response = query_chromadb(query, k=k)
            
            print("\n" + "=" * 80)
            print(f"🤖 Answer:\n{response['result']}")
            print("\n" + "=" * 80)
            print(f"📚 Analyzed {len(response['source_documents'])} influencer(s)")
            
        elif mode == "2":
            # Similarity Search
            query = input("\n🔍 Enter search query: ").strip()
            if not query or query.lower() in ["exit", "quit"]:
                continue
            
            k = input("Number of results (default 5): ").strip()
            k = int(k) if k.isdigit() else 5
            
            results = similarity_search(query, k=k)
            print_search_results(results)
            
        elif mode == "3":
            # Rising Stars
            query = input("\n⭐ Enter category/niche (or press Enter for all): ").strip()
            query = query if query else "rising influencers"
            
            min_eng = input("Minimum engagement rate % (default 3.0): ").strip()
            min_eng = float(min_eng) if min_eng else 3.0
            
            k = input("Number of results (default 10): ").strip()
            k = int(k) if k.isdigit() else 10
            
            results = find_rising_stars(query=query, min_engagement=min_eng, k=k)
            print_search_results(results)
            
        elif mode == "4":
            # Top Influencers
            query = input("\n🏆 Enter category/niche (or press Enter for all): ").strip()
            query = query if query else "top influencers"
            
            min_followers = input("Minimum followers (default 100000): ").strip()
            min_followers = int(min_followers) if min_followers.isdigit() else 100000
            
            k = input("Number of results (default 10): ").strip()
            k = int(k) if k.isdigit() else 10
            
            results = find_top_influencers(query=query, min_followers=min_followers, k=k)
            print_search_results(results)
            
        elif mode == "5":
            # Specific Influencer
            username = input("\n👤 Enter username (with or without @): ").strip()
            if not username or username.lower() in ["exit", "quit"]:
                continue
            
            summary = get_influencer_summary(username)
            
            if summary:
                print("\n" + "=" * 80)
                print(f"📊 Influencer Profile: @{summary['username']}")
                print("=" * 80)
                print(f"Name: {summary['name']}")
                print(f"Followers: {summary['followers']:,}")
                print(f"Engagement Rate: {summary['engagement_rate']:.2f}%")
                print(f"Category: {summary['category']}")
                print(f"Location: {summary['location']}")
                if summary['top_hashtags']:
                    hashtags = ", ".join([f"#{tag}" for tag in summary['top_hashtags']])
                    print(f"Top Hashtags: {hashtags}")
                print(f"\nBio/Description:\n{summary['content']}")
                print("=" * 80)
            else:
                print(f"\n❌ Influencer '@{username}' not found in database.")
                
        elif mode == "6":
            # Compare Influencers
            print("\n📊 Enter usernames to compare (comma-separated):")
            usernames_input = input("Usernames: ").strip()
            if not usernames_input or usernames_input.lower() in ["exit", "quit"]:
                continue
            
            usernames = [u.strip() for u in usernames_input.split(",")]
            results = compare_influencers(usernames)
            
            if results:
                print("\n" + "=" * 80)
                print(f"📊 Comparing {len(results)} Influencer(s)")
                print("=" * 80)
                
                for i, summary in enumerate(results, 1):
                    print(f"\n{i}. @{summary['username']}")
                    print(f"   Name: {summary['name']}")
                    print(f"   Followers: {summary['followers']:,}")
                    print(f"   Engagement: {summary['engagement_rate']:.2f}%")
                    print(f"   Category: {summary['category']}")
                    print(f"   Location: {summary['location']}")
                    print("-" * 80)
            else:
                print("\n❌ No influencers found with those usernames.")
        
        else:
            print("\n❌ Invalid option. Please choose 0-6.")


if __name__ == "__main__":
    # Run interactive mode
    interactive_query()
