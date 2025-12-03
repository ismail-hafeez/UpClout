"""
Embeds data from Postgres DB and stores it in ChromaDB using LangChain.
Computes metrics on-the-fly: engagement rate, avg likes/comments, hashtag frequency.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any
import os
import sys
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# File import
from config.vertex_config import vector_store, embeddings
from src.etl.load import Postgres

# Configuration
PROCESSED_LOG_PATH = "processed_ids.txt"
CHUNK_SIZE = 1000  # Reduced to stay within 20K token limit
CHUNK_OVERLAP = 100
BATCH_SIZE = 50  # ChromaDB works well with smaller batches
MAX_RECENT_POSTS = 20  # Number of recent posts to include per influencer


def load_processed_ids(log_path: str = PROCESSED_LOG_PATH) -> set:
    """Load previously processed influencer IDs to avoid duplicates."""
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
    """Save processed influencer IDs to log file."""
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for doc_id in processed_ids:
            f.write(f"{doc_id}\n")


def get_influencer_posts(db: Postgres, influencer_id: int, limit: int = MAX_RECENT_POSTS) -> List[Dict]:
    """
    Get recent posts for an influencer with hashtags.
    
    Returns:
        List of post dictionaries with caption, likes, comments, hashtags, etc.
    """
    query = """
        SELECT 
            p.postid,
            p.caption,
            p.likescount,
            p.commentscount,
            p.timestamp,
            p.issponsored,
            p.type,
            ARRAY_AGG(h.tag_name) FILTER (WHERE h.tag_name IS NOT NULL) as hashtags
        FROM posts p
        LEFT JOIN posts_hashtags ph ON p.postid = ph.post_id
        LEFT JOIN hashtags h ON ph.hashtag_id = h.hashtagid
        WHERE p.ownerid = %s
        GROUP BY p.postid, p.caption, p.likescount, p.commentscount, p.timestamp, p.issponsored, p.type
        ORDER BY p.timestamp DESC
        LIMIT %s
    """
    
    results = db.execute(query, (influencer_id, limit))
    return results if results else []


def compute_metrics(posts: List[Dict], followers: int) -> Dict[str, Any]:
    """
    Compute engagement metrics from raw post data.
    
    Args:
        posts: List of post dictionaries
        followers: Follower count
        
    Returns:
        Dictionary with computed metrics
    """
    if not posts:
        return {
            "avg_likes": 0,
            "avg_comments": 0,
            "total_engagement": 0,
            "engagement_rate": 0.0,
            "sponsored_count": 0,
            "post_count": 0
        }
    
    total_likes = sum(p.get('likescount', 0) or 0 for p in posts)
    total_comments = sum(p.get('commentscount', 0) or 0 for p in posts)
    sponsored_count = sum(1 for p in posts if p.get('issponsored', False))
    post_count = len(posts)
    
    avg_likes = total_likes / post_count if post_count > 0 else 0
    avg_comments = total_comments / post_count if post_count > 0 else 0
    total_engagement = total_likes + total_comments
    
    # Engagement rate: (avg likes + avg comments) / followers * 100
    engagement_rate = ((avg_likes + avg_comments) / followers * 100) if followers > 0 else 0.0
    
    return {
        "avg_likes": round(avg_likes, 2),
        "avg_comments": round(avg_comments, 2),
        "total_engagement": total_engagement,
        "engagement_rate": round(engagement_rate, 3),
        "sponsored_count": sponsored_count,
        "post_count": post_count
    }


def get_top_hashtags(posts: List[Dict], top_n: int = 10) -> List[tuple]:
    """
    Extract and count hashtags from posts.
    
    Returns:
        List of (hashtag, count) tuples
    """
    hashtag_counter = Counter()
    
    for post in posts:
        hashtags = post.get('hashtags', [])
        if hashtags and hashtags != [None]:
            for tag in hashtags:
                if tag:
                    hashtag_counter[tag] += 1
    
    return hashtag_counter.most_common(top_n)


def format_influencer_document(influencer: Dict, posts: List[Dict], metrics: Dict, top_hashtags: List[tuple]) -> str:
    """
    Format influencer data into rich text for semantic search.
    
    Creates a comprehensive text representation including:
    - Profile information
    - Computed metrics
    - Top hashtags
    - Recent post captions
    """
    # Basic profile info
    name = influencer.get('name', 'Unknown')
    username = influencer.get('username', 'unknown')
    bio = influencer.get('bio', 'No bio available')
    followers = influencer.get('followers', 0)
    following = influencer.get('following', 0)
    location = influencer.get('location', 'Unknown')
    category = influencer.get('businesscategoryname', 'Uncategorized')
    is_verified = influencer.get('isverified', False)
    
    # Build document text
    doc_parts = []
    
    # Header
    doc_parts.append(f"Influencer Profile: @{username}")
    if name and name != username:
        doc_parts.append(f"Name: {name}")
    
    if is_verified:
        doc_parts.append("✓ Verified Account")
    
    # Bio
    if bio and bio != 'No bio available':
        doc_parts.append(f"\nBio: {bio}")
    
    # Category and Location
    doc_parts.append(f"\nCategory: {category}")
    doc_parts.append(f"Location: {location}")
    
    # Metrics
    doc_parts.append(f"\n--- Metrics ---")
    doc_parts.append(f"Followers: {followers:,}")
    doc_parts.append(f"Following: {following:,}")
    doc_parts.append(f"Engagement Rate: {metrics['engagement_rate']:.2f}%")
    doc_parts.append(f"Average Likes: {metrics['avg_likes']:,.0f}")
    doc_parts.append(f"Average Comments: {metrics['avg_comments']:,.0f}")
    doc_parts.append(f"Total Posts Analyzed: {metrics['post_count']}")
    
    if metrics['sponsored_count'] > 0:
        doc_parts.append(f"Sponsored Posts: {metrics['sponsored_count']}")
    
    # Top Hashtags
    if top_hashtags:
        hashtag_str = ", ".join([f"#{tag} ({count})" for tag, count in top_hashtags[:5]])
        doc_parts.append(f"\nTop Hashtags: {hashtag_str}")
    
    # Recent Posts (captions only, for semantic understanding)
    if posts:
        doc_parts.append(f"\n--- Recent Post Captions ---")
        for i, post in enumerate(posts[:10], 1):  # Include top 10 captions
            caption = post.get('caption', '')
            if caption and len(caption.strip()) > 0:
                # Truncate very long captions
                caption_preview = caption[:200] + "..." if len(caption) > 200 else caption
                doc_parts.append(f"{i}. {caption_preview}")
    
    return "\n".join(doc_parts)


def load_documents_from_postgres(already_processed: set) -> List[Document]:
    """
    Load influencer documents from Postgres database with computed metrics.
    
    Args:
        already_processed: Set of already processed influencer IDs
        
    Returns:
        List of LangChain Document objects
    """
    db = Postgres()
    docs = []
    
    # Build exclusion clause
    if already_processed:
        processed_list = ",".join(already_processed)
        exclusion_clause = f"WHERE i.influencerid NOT IN ({processed_list})"
    else:
        exclusion_clause = ""
    
    # Query all influencers
    query = f"""
        SELECT 
            i.influencerid,
            i.name,
            i.username,
            i.bio,
            i.followers,
            i.following,
            i.location,
            i.businesscategoryname,
            i.postcount,
            i.isverified,
            i.isbusinessaccount,
            i.profile_pic,
            i.url
        FROM influencers i
        {exclusion_clause}
        ORDER BY i.followers DESC
    """
    
    # Use the execute() method which returns list of dictionaries
    influencers = db.execute(query)
    
    if not influencers:
        print("No new influencers found.")
        return docs
    
    print(f"Processing {len(influencers)} influencers...")
    
    for idx, influencer in enumerate(influencers, 1):
        influencer_id = influencer['influencerid']
        username = influencer.get('username', 'unknown')
        followers = influencer.get('followers', 0)
        
        # Get posts for this influencer
        posts = get_influencer_posts(db, influencer_id)
        
        # Compute metrics
        metrics = compute_metrics(posts, followers)
        
        # Get top hashtags
        top_hashtags = get_top_hashtags(posts)
        
        # Format document
        page_content = format_influencer_document(influencer, posts, metrics, top_hashtags)
        
        # Create metadata
        metadata = {
            "id": str(influencer_id),
            "type": "influencer",
            "username": username,
            "name": influencer.get('name', ''),
            "followers": followers,
            "following": influencer.get('following', 0),
            "engagement_rate": metrics['engagement_rate'],
            "avg_likes": metrics['avg_likes'],
            "avg_comments": metrics['avg_comments'],
            "location": influencer.get('location', ''),
            "category": influencer.get('businesscategoryname', ''),
            "is_verified": influencer.get('isverified', False),
            "post_count": metrics['post_count'],
            "sponsored_count": metrics['sponsored_count'],
            "top_hashtags": ", ".join([tag for tag, _ in top_hashtags[:5]]) if top_hashtags else ""
        }
        
        # Create Document
        docs.append(Document(
            page_content=page_content,
            metadata=metadata
        ))
        
        if idx % 10 == 0:
            print(f"  Processed {idx}/{len(influencers)} influencers...")
    
    print(f"✓ Loaded {len(docs)} influencer documents with computed metrics.")
    return docs


def split_documents(documents: List[Document], 
                    chunk_size: int = CHUNK_SIZE, 
                    chunk_overlap: int = CHUNK_OVERLAP) -> List[Document]:
    """
    Split documents into smaller chunks for better embedding quality.
    
    Note: For influencer profiles, we may want to keep them whole
    rather than splitting, as the context is important.
    """
    # Split documents to stay within embedding model token limits (20K tokens)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks
    # text_splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap,
    #     length_function=len,
    #     add_start_index=True,
    # )
    # chunks = text_splitter.split_documents(documents)
    # print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    # return chunks


def embed_to_chromadb(chunks: List[Document], batch_size: int = BATCH_SIZE) -> None:
    """
    Embed document chunks and store them in ChromaDB.
    
    Args:
        chunks: List of Document chunks to embed
        batch_size: Number of documents to process in each batch
    """
    try:
        total_chunks = len(chunks)
        print(f"Starting to embed {total_chunks} documents to ChromaDB...")
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            
            # Add documents to ChromaDB (embeddings are generated automatically)
            vector_store.add_documents(batch)
            
            print(f"✓ Added batch {i//batch_size + 1}: {len(batch)} documents (Total: {min(i+batch_size, total_chunks)}/{total_chunks})")
        
        print(f"✓ Successfully embedded {total_chunks} documents to ChromaDB.")
        
    except Exception as e:
        print(f"✗ Error adding documents to ChromaDB: {e}")
        raise


def main():
    """
    Main execution function for embedding pipeline.
    """
    print("=" * 60)
    print("ChromaDB Embedding Pipeline - Influencer Data")
    print("=" * 60)
    
    # Load already processed influencer IDs
    already_processed = load_processed_ids()
    print(f"Found {len(already_processed)} already processed influencers.")
    
    # Load new documents from Postgres
    print("\nLoading influencer data from Postgres...")
    new_documents = load_documents_from_postgres(already_processed)
    
    if not new_documents:
        print("✓ No new influencers to embed. Exiting.")
        return
    
    print(f"✓ Loaded {len(new_documents)} new influencer profiles.")
    
    # Split documents into chunks (currently disabled for influencer profiles)
    print("\nPreparing documents...")
    chunks = split_documents(new_documents)
    
    # Embed and store in ChromaDB
    print("\nEmbedding documents to ChromaDB...")
    embed_to_chromadb(chunks)
    
    # Save newly processed influencer IDs
    new_ids = set(doc.metadata.get("id", "") for doc in new_documents if doc.metadata.get("id"))
    all_processed = already_processed | new_ids
    save_processed_ids(all_processed)
    print(f"\n✓ Saved {len(new_ids)} new processed influencer IDs.")
    
    print("\n" + "=" * 60)
    print("Embedding Pipeline Completed Successfully!")
    print(f"Total influencers in ChromaDB: {len(all_processed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
