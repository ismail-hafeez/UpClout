import psycopg2
import sys
import os

# Add relevant paths for imports
sys.path.append(r"c:\Users\ismai\OneDrive\Desktop\UpClout\backend-fastapi")

from app.chatbot import llm

def get_db():
    return psycopg2.connect(database="postgres", user="postgres", password="1040")

def dry_run():
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Fetch the 'Universe' of valid categories
    cur.execute("""
        SELECT DISTINCT businesscategoryname 
        FROM brands 
        WHERE businesscategoryname IS NOT NULL 
          AND businesscategoryname NOT LIKE 'None,%'
          AND businesscategoryname != 'nan';
    """)
    categories = [row[0] for row in cur.fetchall()]
    print(f"Total categories in universe: {len(categories)}")
    
    # 2. Fetch 5 sample influencers with missing categories
    cur.execute("""
        SELECT i.brandid, i.username, i.name, i.bio, i.businesscategoryname,
               (SELECT string_agg(caption, ' | ') FROM (SELECT caption FROM posts WHERE ownerbrandid = i.brandid LIMIT 5) p) as captions
        FROM brands i
        WHERE (businesscategoryname IS NULL OR businesscategoryname ILIKE 'None%' OR businesscategoryname ILIKE 'nan%')
          AND bio IS NOT NULL AND bio != '';
    """)
    samples = cur.fetchall()
    
    if not samples:
        print("No samples with missing categories found.")
        return

    print("\n--- Starting AI Classification Dry Run ---\n")
    
    for infl_id, username, name, bio, old_cat, captions in samples:

        with open("niche_dry_run_output.txt", "a", encoding="utf-8") as f:
            f.write(f"Processing @{username} ({name})\n")
            f.write(f"  Old Cat: {old_cat}\n")
            f.write(f"  Bio snippet: {bio[:100]}...\n")
        
        prompt = f"""
        You are an AI expert in influencer marketing.
        Based on the profile bio and post captions below, classify this brand profile into EXACTLY ONE category from the provided list.
        If none fit perfectly, pick the closest one.
        
        BIO: {bio}
        CAPTIONS: {captions[:500] if captions else 'N/A'}
        
        CATEGORIES LIST:
        {', '.join(categories)}
        
        Return ONLY the name of the category. No explanation.
        """
        
        try:
            response = llm.invoke(prompt)
            prediction = response.content.strip()
            with open("niche_dry_run_output.txt", "a", encoding="utf-8") as f:
                f.write(f"  --> AI PREDICTION: [{prediction}]\n")
        except Exception as e:
            with open("niche_dry_run_output.txt", "a", encoding="utf-8") as f:
                f.write(f"  Error classifying @{username}: {e}\n")
        with open("niche_dry_run_output.txt", "a", encoding="utf-8") as f:
            f.write("-" * 40 + "\n")

    cur.close()
    conn.close()

if __name__ == "__main__":
    dry_run()
