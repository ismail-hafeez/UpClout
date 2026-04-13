import psycopg2
import sys
import os
import time

# Add relevant paths for backend imports
# Make this more robust to the actual environment
project_root = r"c:\Users\ismai\OneDrive\Desktop\UpClout"
sys.path.append(os.path.join(project_root, "backend-fastapi"))

from app.chatbot import llm
from db_utils import get_connection

def get_db():
    return get_connection()

def get_category_universe(cur):
    """Fetches the list of all valid categories currently in the DB."""
    cur.execute("""
        SELECT DISTINCT businesscategoryname 
        FROM influencers 
        WHERE businesscategoryname IS NOT NULL 
          AND businesscategoryname NOT LIKE 'None,%'
          AND businesscategoryname NOT ILIKE 'nan%'
    """)
    return [row[0] for row in cur.fetchall()]

def fill_missing_niches():
    conn = get_db()
    cur = conn.cursor()
    
    universe = get_category_universe(cur)
    if not universe:
        print("No valid categories found to match against. Existing.")
        return
        
    print(f"Loaded {len(universe)} categories into universe.")
    
    # 1. Fetch all Influencers AND Brands with missing categories
    # We do them in one script.
    
    targets = [
        ("Influencers", "influencerid"),
        ("Brands", "brandid")
    ]
    
    for table, id_col in targets:
        print(f"\n--- Processing {table} ---")
        
        # Fetch targets with bio/captions
        # Join with posts to get captions for better guessing
        query = f"""
            SELECT i.{id_col}, i.username, i.bio,
                   (SELECT string_agg(caption, ' | ') FROM (SELECT caption FROM posts WHERE (ownerid = i.{id_col} OR ownerbrandid = i.{id_col}) LIMIT 10) p) as captions
            FROM {table} i
            WHERE (businesscategoryname IS NULL OR businesscategoryname ILIKE 'None%' OR businesscategoryname ILIKE 'nan%')
              AND (bio IS NOT NULL AND bio != '')
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} {table} requiring categorization.")
        
        for record_id, username, bio, captions in rows:
            print(f"Categorizing @{username}...")
            
            prompt = f"""
            You are an AI expert in social media marketing. 
            Classify this profile into EXACTLY ONE category from the provided list based on their bio and last few captions.
            
            USER BIO: {bio}
            CAPTIONS: {captions[:1000] if captions else 'N/A'}
            
            LIST OF VALID CATEGORIES:
            {', '.join(universe)}
            
            Return ONLY the verbatim category name from the list. If none fit, return 'Personal blog'.
            """
            
            try:
                response = llm.invoke(prompt)
                predicted = response.content.strip().replace("[", "").replace("]", "")
                
                # Update the database
                update_query = f"UPDATE {table} SET businesscategoryname = %s WHERE {id_col} = %s"
                cur.execute(update_query, (predicted, record_id))
                conn.commit()
                print(f"  -> Assigned: {predicted}")
                
                # Small delay to respect rate limits if needed
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Error categorizing {username}: {e}")
                conn.rollback()

    cur.close()
    conn.close()
    print("\n--- Niche Filling Complete ---")

if __name__ == "__main__":
    fill_missing_niches()
