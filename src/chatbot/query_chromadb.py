"""
Query ChromaDB using LangChain for semantic search with Gemini 2.5 Flash.
Example usage of the RAG pipeline.
"""

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
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


def similarity_search(query: str, k: int = 5) -> list:
    """
    Perform direct similarity search without LLM generation.
    
    Args:
        query: Search query
        k: Number of results to return
        
    Returns:
        List of relevant documents
    """
    results = vector_store.similarity_search(query, k=k)
    return results


def similarity_search_with_score(query: str, k: int = 5) -> list:
    """
    Perform similarity search with relevance scores.
    
    Args:
        query: Search query
        k: Number of results to return
        
    Returns:
        List of tuples (document, score)
    """
    results = vector_store.similarity_search_with_score(query, k=k)
    return results


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("ChromaDB Query Example")
    print("=" * 60)
    
    # Example query
    test_query = "Show me top influencers with high engagement rate"
    
    print(f"\nQuery: {test_query}\n")
    
    # Method 1: RAG with LLM
    print("\n--- RAG Response (with Gemini 2.5 Flash) ---")
    response = query_chromadb(test_query, k=3)
    print(f"Answer: {response['result']}")
    print(f"\nSources: {len(response['source_documents'])} documents retrieved")
    
    # Method 2: Direct similarity search
    print("\n--- Direct Similarity Search ---")
    docs = similarity_search(test_query, k=3)
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. {doc.page_content[:200]}...")
        print(f"   Metadata: {doc.metadata}")
    
    # Method 3: Similarity search with scores
    print("\n--- Similarity Search with Scores ---")
    scored_docs = similarity_search_with_score(test_query, k=3)
    for i, (doc, score) in enumerate(scored_docs, 1):
        print(f"\n{i}. Score: {score:.4f}")
        print(f"   Content: {doc.page_content[:200]}...")
        print(f"   Metadata: {doc.metadata}")
