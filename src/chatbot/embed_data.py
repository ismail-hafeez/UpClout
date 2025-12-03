"""
Embeds data from Postgres DB and stores it in ChromaDB using LangChain.
This is a boilerplate template - update with actual Postgres queries.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List
import os

# File import
from config.vertex_config import vector_store, embeddings

# TODO: Update with your actual Postgres connection
# Example placeholder for Postgres connection
# from src.load import Postgres

# Configuration
PROCESSED_LOG_PATH = "../data/processed_ids.txt"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 120
BATCH_SIZE = 100  # ChromaDB works well with smaller batches


def load_processed_ids(log_path: str = PROCESSED_LOG_PATH) -> set:
    """
    Load previously processed document IDs to avoid duplicates.
    
    Args:
        log_path: Path to the log file containing processed IDs
        
    Returns:
        Set of processed document IDs
    """
    processed_ids = set()
    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    processed_ids.add(line.strip())
    except FileNotFoundError:
        pass
    return processed_ids


def save_processed_ids(processed_ids: set, log_path: str = PROCESSED_LOG_PATH) -> None:
    """
    Save processed document IDs to log file.
    
    Args:
        processed_ids: Set of processed document IDs
        log_path: Path to the log file
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for doc_id in processed_ids:
            f.write(f"{doc_id}\n")


def load_documents_from_postgres(already_processed: set) -> List[Document]:
    """
    Load documents from Postgres database.
    
    TODO: Replace this boilerplate with your actual Postgres query logic.
    
    Args:
        already_processed: Set of already processed document IDs
        
    Returns:
        List of LangChain Document objects
        
    Example implementation:
    ```python
    from src.load import Postgres
    
    db = Postgres()
    query = '''
        SELECT id, username, bio, followers_count, engagement_rate, category
        FROM instagram_profiles
        WHERE id NOT IN %(processed_ids)s
    '''
    results = db.execute(query, {'processed_ids': tuple(already_processed)})
    
    docs = []
    for row in results:
        # Create meaningful text content from profile data
        page_content = f'''
        Username: {row['username']}
        Bio: {row['bio']}
        Followers: {row['followers_count']}
        Engagement Rate: {row['engagement_rate']}%
        Category: {row['category']}
        '''
        
        docs.append(Document(
            page_content=page_content.strip(),
            metadata={
                "id": str(row['id']),
                "username": row['username'],
                "followers_count": row['followers_count'],
                "engagement_rate": row['engagement_rate'],
                "category": row['category']
            }
        ))
    
    return docs
    ```
    """
    # BOILERPLATE: Replace with actual Postgres query
    docs = []
    
    # Example placeholder structure
    # db = Postgres()
    # query = "SELECT * FROM your_table WHERE id NOT IN %(processed_ids)s"
    # results = db.execute(query, {'processed_ids': tuple(already_processed)})
    
    # for row in results:
    #     page_content = f"Your formatted content from row: {row}"
    #     docs.append(Document(
    #         page_content=page_content,
    #         metadata={
    #             "id": str(row['id']),
    #             # Add other relevant metadata fields
    #         }
    #     ))
    
    return docs


def split_documents(documents: List[Document], 
                    chunk_size: int = CHUNK_SIZE, 
                    chunk_overlap: int = CHUNK_OVERLAP) -> List[Document]:
    """
    Split documents into smaller chunks for better embedding quality.
    
    Args:
        documents: List of Document objects to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between consecutive chunks
        
    Returns:
        List of chunked Document objects
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks


def embed_to_chromadb(chunks: List[Document], batch_size: int = BATCH_SIZE) -> None:
    """
    Embed document chunks and store them in ChromaDB.
    
    Args:
        chunks: List of Document chunks to embed
        batch_size: Number of documents to process in each batch
    """
    try:
        total_chunks = len(chunks)
        print(f"Starting to embed {total_chunks} chunks to ChromaDB...")
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            
            # Add documents to ChromaDB (embeddings are generated automatically)
            vector_store.add_documents(batch)
            
            print(f"✓ Added batch {i//batch_size + 1}: {len(batch)} chunks (Total: {min(i+batch_size, total_chunks)}/{total_chunks})")
        
        print(f"✓ Successfully embedded {total_chunks} chunks to ChromaDB.")
        
    except Exception as e:
        print(f"✗ Error adding documents to ChromaDB: {e}")
        raise


def main():
    """
    Main execution function for embedding pipeline.
    """
    print("=" * 60)
    print("Starting ChromaDB Embedding Pipeline")
    print("=" * 60)
    
    # Load already processed document IDs
    already_processed = load_processed_ids()
    print(f"Found {len(already_processed)} already processed documents.")
    
    # Load new documents from Postgres
    print("\nLoading documents from Postgres...")
    new_documents = load_documents_from_postgres(already_processed)
    
    if not new_documents:
        print("✓ No new documents to embed. Exiting.")
        return
    
    print(f"✓ Loaded {len(new_documents)} new documents.")
    
    # Split documents into chunks
    print("\nSplitting documents into chunks...")
    chunks = split_documents(new_documents)
    
    # Embed and store in ChromaDB
    print("\nEmbedding chunks to ChromaDB...")
    embed_to_chromadb(chunks)
    
    # Save newly processed document IDs
    new_ids = set(doc.metadata.get("id", "") for doc in new_documents if doc.metadata.get("id"))
    all_processed = already_processed | new_ids
    save_processed_ids(all_processed)
    print(f"\n✓ Saved {len(new_ids)} new processed document IDs.")
    
    print("\n" + "=" * 60)
    print("Embedding Pipeline Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()