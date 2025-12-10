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


def classify_intent(query: str) -> Dict[str, Any]:
    """
    Classify user intent and extract parameters using LLM.
    
    Args:
        query: User's natural language query
        
    Returns:
        Dictionary with intent type and extracted parameters
    """
    classification_prompt = f"""Analyze this user query and classify the intent. Extract relevant parameters.

User Query: "{query}"

Classify into ONE of these intents:
1. GENERAL_CHAT - General questions, RAG-based answers
2. RISING_STARS - Looking for rising influencers (high engagement, 10K-100K followers)
3. TOP_INFLUENCERS - Looking for top-tier influencers (100K+ followers)
4. SPECIFIC_LOOKUP - Looking up a specific influencer by username
5. COMPARE - Comparing multiple influencers
6. SIMILARITY_SEARCH - Finding similar influencers based on description

Extract these parameters if mentioned:
- usernames: List of @usernames mentioned
- category/niche: Business category (fitness, beauty, tech, etc.)
- min_followers: Minimum follower count
- max_followers: Maximum follower count
- min_engagement: Minimum engagement rate percentage
- num_results: Number of results requested (default 5 for specific queries. IF "list" or "all" is mentioned, set to 20 or higher. Max 50.)
- location: Geographic location if mentioned

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
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response (in case LLM adds extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            # Fallback to general chat
            return {
                "intent": "GENERAL_CHAT",
                "parameters": {"num_results": 5},
                "original_query": query
            }
    except Exception as e:
        print(f"⚠️ Intent classification error: {e}")
        return {
            "intent": "GENERAL_CHAT",
            "parameters": {"num_results": 5},
            "original_query": query
        }


def route_query(query: str) -> str:
    """
    Route user query to appropriate function based on intent.
    
    Args:
        query: User's natural language query
        
    Returns:
        Formatted response string
    """
    # Classify intent
    classification = classify_intent(query)
    intent = classification.get("intent", "GENERAL_CHAT")
    params = classification.get("parameters", {})
    
    print(f"\n🤔 Understanding your request... (Intent: {intent})")
    
    try:
        if intent == "SPECIFIC_LOOKUP":
            # Look up specific influencer
            usernames = params.get("usernames", [])
            if not usernames:
                return "❌ Please specify an influencer username (e.g., @username)"
            
            username = usernames[0]
            summary = get_influencer_summary(username)
            
            if summary:
                response = f"\n{'=' * 80}\n"
                response += f"📊 Influencer Profile: @{summary['username']}\n"
                response += f"{'=' * 80}\n"
                response += f"Name: {summary['name']}\n"
                response += f"Followers: {summary['followers']:,}\n"
                response += f"Engagement Rate: {summary['engagement_rate']:.2f}%\n"
                response += f"Category: {summary['category']}\n"
                response += f"Location: {summary['location']}\n"
                if summary['top_hashtags']:
                    hashtags = ", ".join([f"#{tag}" for tag in summary['top_hashtags']])
                    response += f"Top Hashtags: {hashtags}\n"
                response += f"\nBio/Description:\n{summary['content']}\n"
                response += f"{'=' * 80}"
                return response
            else:
                return f"❌ Influencer '@{username}' not found in database."
        
        elif intent == "COMPARE":
            # Compare multiple influencers
            usernames = params.get("usernames", [])
            if len(usernames) < 2:
                return "❌ Please specify at least 2 usernames to compare (e.g., 'compare @user1 and @user2')"
            
            results = compare_influencers(usernames)
            
            if results:
                response = f"\n{'=' * 80}\n"
                response += f"📊 Comparing {len(results)} Influencer(s)\n"
                response += f"{'=' * 80}\n"
                
                for i, summary in enumerate(results, 1):
                    response += f"\n{i}. @{summary['username']}\n"
                    response += f"   Name: {summary['name']}\n"
                    response += f"   Followers: {summary['followers']:,}\n"
                    response += f"   Engagement: {summary['engagement_rate']:.2f}%\n"
                    response += f"   Category: {summary['category']}\n"
                    response += f"   Location: {summary['location']}\n"
                    response += f"{'-' * 80}\n"
                return response
            else:
                return "❌ No influencers found with those usernames."
        
        elif intent == "RISING_STARS":
            # Find rising stars
            category = params.get("category", "rising influencers")
            min_engagement = params.get("min_engagement", 3.0)
            num_results = params.get("num_results", 10)
            
            query_text = f"{category} rising influencers" if category else "rising influencers"
            results = find_rising_stars(query=query_text, min_engagement=min_engagement, k=num_results)
            
            if results:
                response = f"\n{'=' * 80}\n"
                response += f"⭐ Found {len(results)} Rising Star Influencers\n"
                response += f"{'=' * 80}\n"
                for i, doc in enumerate(results, 1):
                    response += f"\n{i}. @{doc.metadata.get('username', 'Unknown')}\n"
                    response += f"   Name: {doc.metadata.get('name', 'N/A')}\n"
                    response += f"   Followers: {doc.metadata.get('followers', 0):,}\n"
                    response += f"   Engagement: {doc.metadata.get('engagement_rate', 0):.2f}%\n"
                    response += f"   Category: {doc.metadata.get('category', 'N/A')}\n"
                    response += f"{'-' * 80}\n"
                return response
            else:
                return "❌ No rising stars found matching your criteria."
        
        elif intent == "TOP_INFLUENCERS":
            # Find top influencers
            category = params.get("category", "top influencers")
            min_followers = params.get("min_followers", 100000)
            num_results = params.get("num_results", 10)
            
            query_text = f"{category} top influencers" if category else "top influencers"
            results = find_top_influencers(query=query_text, min_followers=min_followers, k=num_results)
            
            if results:
                response = f"\n{'=' * 80}\n"
                response += f"🏆 Found {len(results)} Top Influencers\n"
                response += f"{'=' * 80}\n"
                for i, doc in enumerate(results, 1):
                    response += f"\n{i}. @{doc.metadata.get('username', 'Unknown')}\n"
                    response += f"   Name: {doc.metadata.get('name', 'N/A')}\n"
                    response += f"   Followers: {doc.metadata.get('followers', 0):,}\n"
                    response += f"   Engagement: {doc.metadata.get('engagement_rate', 0):.2f}%\n"
                    response += f"   Category: {doc.metadata.get('category', 'N/A')}\n"
                    response += f"{'-' * 80}\n"
                return response
            else:
                return "❌ No top influencers found matching your criteria."
        
        elif intent == "SIMILARITY_SEARCH":
            # Similarity search
            num_results = params.get("num_results", 5)
            results = similarity_search(query, k=num_results)
            
            if results:
                response = f"\n{'=' * 80}\n"
                response += f"🔍 Found {len(results)} Similar Influencers\n"
                response += f"{'=' * 80}\n"
                for i, doc in enumerate(results, 1):
                    response += f"\n{i}. @{doc.metadata.get('username', 'Unknown')}\n"
                    response += f"   Name: {doc.metadata.get('name', 'N/A')}\n"
                    response += f"   Followers: {doc.metadata.get('followers', 0):,}\n"
                    response += f"   Engagement: {doc.metadata.get('engagement_rate', 0):.2f}%\n"
                    response += f"   Category: {doc.metadata.get('category', 'N/A')}\n"
                    response += f"{'-' * 80}\n"
                return response
            else:
                return "❌ No similar influencers found."
        
        else:  # GENERAL_CHAT
            # Use RAG with Gemini
            num_results = params.get("num_results", 5)
            rag_response = query_chromadb(query, k=num_results)
            
            response = f"\n{'=' * 80}\n"
            response += f"🤖 Owly's Answer:\n\n{rag_response['result']}\n"
            response += f"\n{'=' * 80}\n"
            response += f"� Analyzed {len(rag_response['source_documents'])} influencer profile(s)\n"
            return response
            
    except Exception as e:
        return f"❌ Error processing query: {str(e)}"


def interactive_query():
    """
    Conversational chatbot interface with intelligent intent detection.
    No menus - just natural conversation!
    """
    print("=" * 80)
    print("🤖 UpClout Influencer Chatbot - Conversational Mode")
    print("=" * 80)
    print("\nHi! I'm Owly, your UpClout assistant. Ask me anything about influencers!")
    print("\nExamples:")
    print("  • 'Show me rising stars in fitness'")
    print("  • 'Who are the top tech influencers?'")
    print("  • 'Tell me about @username'")
    print("  • 'Compare @user1 and @user2'")
    print("  • 'Find influencers with high engagement in beauty'")
    print("\nType 'exit' or 'quit' to end the session.\n")
    
    conversation_history = []
    
    while True:
        # Get user input
        user_input = input("\n💬 You: ").strip()
        
        # Check for exit
        if not user_input or user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print("\n👋 Thanks for chatting! Goodbye!")
            break
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Route query and get response
        response = route_query(user_input)
        
        # Display response
        print(f"\n{response}")
        
        # Add to conversation history
        conversation_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    # Run interactive mode
    interactive_query()
