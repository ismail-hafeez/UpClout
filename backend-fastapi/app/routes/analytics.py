from fastapi import APIRouter, HTTPException, Depends
from app.auth import get_current_user
import psycopg2
from typing import List, Dict

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/{username}")
async def get_user_analytics(username: str, user: dict = Depends(get_current_user)):
    """Fetches real-time analytics for an influencer from Postgres."""
    # Note: Only a Brand or the user themselves should see details if you want privacy, 
    # but for now we keep it open for the dashboard.
    
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        
        # 0. Identify Target User Type
        cur.execute("SELECT 1 FROM Influencers WHERE username = %s LIMIT 1", (username,))
        is_influencer = cur.fetchone()
        
        if is_influencer:
            join_table = "Influencers"
            join_col = "i.influencerid = p.ownerid"
        else:
            join_table = "Brands"
            join_col = "i.brandid = p.ownerbrandid"
            
        # 1. Top 5 Hashtags
        cur.execute(f"""
            SELECT h.tag_name, COUNT(*) as count 
            FROM Hashtags h
            JOIN posts_hashtags ph ON h.hashtagid = ph.hashtag_id
            JOIN Posts p ON ph.post_id = p.postID
            JOIN {join_table} i ON {join_col}
            WHERE i.username = %s
            GROUP BY h.tag_name
            ORDER BY count DESC
            LIMIT 5;
        """, (username,))
        hashtags = [{"name": row[0], "value": row[1]} for row in cur.fetchall()]
        
        # 2. Top 5 Tagged People (Mentions)
        cur.execute(f"""
            SELECT tu.username, COUNT(*) as count
            FROM taggeduser tu
            JOIN posts_taggeduser ptu ON tu.taggeduserID = ptu.taggeduserID
            JOIN Posts p ON ptu.postID = p.postID
            JOIN {join_table} i ON {join_col}
            WHERE i.username = %s
            GROUP BY tu.username
            ORDER BY count DESC
            LIMIT 5;
        """, (username,))
        mentions = [{"name": row[0], "value": row[1]} for row in cur.fetchall()]
        
        # 3. Monthly Engagement Trends
        cur.execute(f"""
            SELECT TO_CHAR(p.timestamp, 'Mon DD') as date_str, 
                   AVG(p.likesCount + p.commentsCount) as engagement,
                   CAST(p.timestamp AS DATE) as raw_date
            FROM Posts p
            JOIN {join_table} i ON {join_col}
            WHERE i.username = %s
            GROUP BY raw_date, date_str
            ORDER BY raw_date ASC
            LIMIT 15;
        """, (username,))
        trends = [{"date": row[0], "engagement": float(row[1])} for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return {
            "hashtags": hashtags,
            "mentions": mentions,
            "trends": trends
        }
        
    except Exception as e:
        print("Analytics error:", e)
        raise HTTPException(status_code=500, detail="Error fetching analytics")
