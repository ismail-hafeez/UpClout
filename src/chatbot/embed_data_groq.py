"""
Embeds data from Postgres DB and stores it in ChromaDB using LangChain.
Processes both influencers and brands with their posts, hashtags, and metrics.
Uses Groq Llama 3 and Local HuggingFace Embeddings.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any
import os
import sys
from collections import Counter

# Add root and src/etl to path for imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
etl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../etl'))
sys.path.insert(0, root_path)
sys.path.insert(0, etl_path)

# File import - CHANGED TO GROQ CONFIG
from src.chatbot.config.groq_config import vector_store, embeddings
from src.etl.load import Postgres

# Configuration
PROCESSED_LOG_PATH = "processed_ids_groq.txt"
CHUNK_SIZE = 1000  
CHUNK_OVERLAP = 100
BATCH_SIZE = 50  

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


def get_influencer_posts(db: Postgres, influencer_id: int) -> List[Dict]:
    """Get ALL posts for an influencer with hashtags."""
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
    """
    results = db.execute(query, (influencer_id,))
    return results if results else []


def get_brand_posts(db: Postgres, brand_id: int) -> List[Dict]:
    """Get ALL posts for a brand with hashtags."""
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
        WHERE p.ownerbrandid = %s
        GROUP BY p.postid, p.caption, p.likescount, p.commentscount, p.timestamp, p.issponsored, p.type
        ORDER BY p.timestamp DESC
    """
    results = db.execute(query, (brand_id,))
    return results if results else []


def compute_metrics(posts: List[Dict], followers: int) -> Dict[str, Any]:
    """Compute engagement metrics from raw post data."""
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
    """Extract and count hashtags from posts."""
    hashtag_counter = Counter()
    for post in posts:
        hashtags = post.get('hashtags', [])
        if hashtags and hashtags != [None]:
            for tag in hashtags:
                if tag:
                    hashtag_counter[tag] += 1
    return hashtag_counter.most_common(top_n)


def format_influencer_document(influencer: Dict, posts: List[Dict], metrics: Dict, top_hashtags: List[tuple]) -> str:
    """Format influencer data into rich text for semantic search."""
    name = influencer.get('name', 'Unknown')
    username = influencer.get('username', 'unknown')
    bio = influencer.get('bio', 'No bio available')
    followers = influencer.get('followers', 0)
    following = influencer.get('following', 0)
    location = influencer.get('location', 'Unknown')
    category = influencer.get('businesscategoryname', 'Uncategorized')
    is_verified = influencer.get('isverified', False)
    
    doc_parts = []
    doc_parts.append(f"Influencer Profile: @{username}")
    if name and name != username:
        doc_parts.append(f"Name: {name}")
    if is_verified:
        doc_parts.append("✓ Verified Account")
    if bio and bio != 'No bio available':
        doc_parts.append(f"\nBio: {bio}")
    doc_parts.append(f"\nCategory: {category}")
    doc_parts.append(f"Location: {location}")
    doc_parts.append(f"\n--- Metrics ---")
    doc_parts.append(f"Followers: {followers:,}")
    doc_parts.append(f"Following: {following:,}")
    doc_parts.append(f"Engagement Rate: {metrics['engagement_rate']:.2f}%")
    doc_parts.append(f"Average Likes: {metrics['avg_likes']:,.0f}")
    doc_parts.append(f"Average Comments: {metrics['avg_comments']:,.0f}")
    doc_parts.append(f"Total Posts Analyzed: {metrics['post_count']}")
    
    if metrics['sponsored_count'] > 0:
        doc_parts.append(f"Sponsored Posts: {metrics['sponsored_count']}")
    
    if top_hashtags:
        hashtag_str = ", ".join([f"#{tag} ({count})" for tag, count in top_hashtags[:5]])
        doc_parts.append(f"\nTop Hashtags: {hashtag_str}")
    
    if posts:
        doc_parts.append(f"\n--- Post Captions ({len(posts)} posts) ---")
        for i, post in enumerate(posts, 1):
            caption = post.get('caption', '')
            if caption and len(caption.strip()) > 0:
                caption_preview = caption[:200] + "..." if len(caption) > 200 else caption
                doc_parts.append(f"{i}. {caption_preview}")
    
    return "\n".join(doc_parts)


def format_brand_document(brand: Dict, posts: List[Dict], metrics: Dict, top_hashtags: List[tuple]) -> str:
    """Format brand data into rich text for semantic search."""
    name = brand.get('name', 'Unknown')
    username = brand.get('username', 'unknown')
    bio = brand.get('bio', 'No bio available')
    followers = brand.get('followers', 0)
    following = brand.get('following', 0)
    location = brand.get('location', 'Unknown')
    category = brand.get('businesscategoryname', 'Uncategorized')
    is_verified = brand.get('isverified', False)
    
    doc_parts = []
    doc_parts.append(f"Brand Profile: @{username}")
    if name and name != username:
        doc_parts.append(f"Brand Name: {name}")
    if is_verified:
        doc_parts.append("✓ Verified Account")
    if bio and bio != 'No bio available':
        doc_parts.append(f"\nBio: {bio}")
    doc_parts.append(f"\nCategory: {category}")
    doc_parts.append(f"Location: {location}")
    doc_parts.append(f"\n--- Metrics ---")
    doc_parts.append(f"Followers: {followers:,}")
    doc_parts.append(f"Following: {following:,}")
    doc_parts.append(f"Engagement Rate: {metrics['engagement_rate']:.2f}%")
    doc_parts.append(f"Average Likes: {metrics['avg_likes']:,.0f}")
    doc_parts.append(f"Average Comments: {metrics['avg_comments']:,.0f}")
    doc_parts.append(f"Total Posts Analyzed: {metrics['post_count']}")
    
    if metrics['sponsored_count'] > 0:
        doc_parts.append(f"Sponsored Posts: {metrics['sponsored_count']}")
    
    if top_hashtags:
        hashtag_str = ", ".join([f"#{tag} ({count})" for tag, count in top_hashtags[:5]])
        doc_parts.append(f"\nTop Hashtags: {hashtag_str}")
    
    if posts:
        doc_parts.append(f"\n--- Post Captions ({len(posts)} posts) ---")
        for i, post in enumerate(posts, 1):
            caption = post.get('caption', '')
            if caption and len(caption.strip()) > 0:
                caption_preview = caption[:200] + "..." if len(caption) > 200 else caption
                doc_parts.append(f"{i}. {caption_preview}")
    
    return "\n".join(doc_parts)


def load_documents_from_postgres(already_processed: set) -> List[Document]:
    """Load influencer documents from Postgres database with computed metrics."""
    db = Postgres()
    docs = []
    
    if already_processed:
        processed_list = ",".join(already_processed)
        exclusion_clause = f"WHERE i.influencerid NOT IN ({processed_list})"
    else:
        exclusion_clause = ""
    
    query = f"""
        SELECT 
            i.influencerid, i.name, i.username, i.bio, i.followers, i.following, 
            i.location, i.businesscategoryname, i.postcount, i.isverified, 
            i.isbusinessaccount, i.profile_pic, i.url
        FROM influencers i
        {exclusion_clause}
        ORDER BY i.followers DESC
    """
    
    influencers = db.execute(query)
    if not influencers:
        print("No new influencers found.")
        return docs
    
    print(f"Processing {len(influencers)} influencers...")
    
    for idx, influencer in enumerate(influencers, 1):
        influencer_id = influencer['influencerid']
        username = influencer.get('username', 'unknown')
        followers = influencer.get('followers', 0)
        posts = get_influencer_posts(db, influencer_id)
        metrics = compute_metrics(posts, followers)
        top_hashtags = get_top_hashtags(posts)
        page_content = format_influencer_document(influencer, posts, metrics, top_hashtags)
        
        metadata = {
            "id": str(influencer_id),
            "type": "influencer",
            "username": username,
            "name": influencer.get('name', ''),
            "followers": followers,
            "engagement_rate": metrics['engagement_rate'],
            "avg_likes": metrics['avg_likes'],
            "avg_comments": metrics['avg_comments'],
            "location": influencer.get('location', ''),
            "category": influencer.get('businesscategoryname', ''),
            "is_verified": influencer.get('isverified', False),
            "post_count": metrics['post_count']
        }
        
        docs.append(Document(page_content=page_content, metadata=metadata))
        if idx % 10 == 0:
            print(f"  Processed {idx}/{len(influencers)} influencers...")
    
    return docs


def load_brands_from_postgres(already_processed: set) -> List[Document]:
    """Load brand documents from Postgres database with computed metrics."""
    db = Postgres()
    docs = []
    
    if already_processed:
        processed_list = ",".join(already_processed)
        exclusion_clause = f"WHERE b.brandid NOT IN ({processed_list})"
    else:
        exclusion_clause = ""
    
    query = f"""
        SELECT 
            b.brandid, b.name, b.username, b.bio, b.followers, b.following, 
            b.location, b.businesscategoryname, b.postcount, b.isverified, 
            b.isbusinessaccount, b.profile_pic, b.url
        FROM brands b
        {exclusion_clause}
        ORDER BY b.followers DESC
    """
    
    brands = db.execute(query)
    if not brands:
        print("No new brands found.")
        return docs
    
    print(f"Processing {len(brands)} brands...")
    
    for idx, brand in enumerate(brands, 1):
        brand_id = brand['brandid']
        username = brand.get('username', 'unknown')
        followers = brand.get('followers', 0)
        posts = get_brand_posts(db, brand_id)
        metrics = compute_metrics(posts, followers)
        top_hashtags = get_top_hashtags(posts)
        page_content = format_brand_document(brand, posts, metrics, top_hashtags)
        
        metadata = {
            "id": str(brand_id),
            "type": "brand",
            "username": username,
            "name": brand.get('name', ''),
            "followers": followers,
            "engagement_rate": metrics['engagement_rate'],
            "avg_likes": metrics['avg_likes'],
            "avg_comments": metrics['avg_comments'],
            "location": brand.get('location', ''),
            "category": brand.get('businesscategoryname', ''),
            "is_verified": brand.get('isverified', False),
            "post_count": metrics['post_count']
        }
        
        docs.append(Document(page_content=page_content, metadata=metadata))
        if idx % 10 == 0:
            print(f"  Processed {idx}/{len(brands)} brands...")
            
    return docs


def split_documents(documents: List[Document], chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[Document]:
    """Split documents into smaller chunks for better embedding quality."""
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
    """Embed document chunks and store them in ChromaDB."""
    try:
        total_chunks = len(chunks)
        print(f"Starting to embed {total_chunks} documents to ChromaDB (Groq Edition)...")
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            vector_store.add_documents(batch)
            print(f"✓ Added batch {i//batch_size + 1}: {len(batch)} documents (Total: {min(i+batch_size, total_chunks)}/{total_chunks})")
        print(f"✓ Successfully embedded {total_chunks} documents to ChromaDB.")
    except Exception as e:
        print(f"✗ Error adding documents to ChromaDB: {e}")
        raise


def main():
    """Main execution function for embedding pipeline."""
    print("=" * 60)
    print("ChromaDB Embedding Pipeline (Groq & Free Embeddings)")
    print("=" * 60)
    
    all_documents = []
    
    # Process Influencers
    already_processed_influencers = load_processed_ids("processed_influencer_ids_groq.txt")
    new_influencer_docs = load_documents_from_postgres(already_processed_influencers)
    if new_influencer_docs:
        all_documents.extend(new_influencer_docs)
    
    # Process Brands
    already_processed_brands = load_processed_ids("processed_brand_ids_groq.txt")
    new_brand_docs = load_brands_from_postgres(already_processed_brands)
    if new_brand_docs:
        all_documents.extend(new_brand_docs)
    
    if not all_documents:
        print("\n✓ No new documents to embed. Exiting.")
        return
    
    chunks = split_documents(all_documents)
    embed_to_chromadb(chunks)
    
    # Save processed IDs
    if new_influencer_docs:
        new_ids = set(doc.metadata.get("id", "") for doc in new_influencer_docs if doc.metadata.get("id"))
        all_ids = already_processed_influencers | new_ids
        save_processed_ids(all_ids, "processed_influencer_ids_groq.txt")
        
    if new_brand_docs:
        new_ids = set(doc.metadata.get("id", "") for doc in new_brand_docs if doc.metadata.get("id"))
        all_ids = already_processed_brands | new_ids
        save_processed_ids(all_ids, "processed_brand_ids_groq.txt")
    
    print("\n✓ Embedding Pipeline Completed Successfully!")


if __name__ == "__main__":
    main()
