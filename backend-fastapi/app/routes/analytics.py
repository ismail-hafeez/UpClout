from fastapi import APIRouter, HTTPException, Depends
from app.auth import get_current_user
from app.database import get_db
import psycopg2
from typing import List, Dict
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/rising-stars")
async def get_rising_stars(user: dict = Depends(get_current_user)):
    """Finds micro-influencers with high engagement velocity."""
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        
        # Query for influencers with 1k - 100k followers and high engagement ratio on recent posts
        query = """
        SELECT i.influencerid, i.name, i.username, i.followers, i.profile_pic, i.businesscategoryname,
               AVG(p.likesCount + p.commentsCount) / NULLIF(i.followers, 0) as momentum
        FROM Influencers i
        JOIN Posts p ON i.influencerid = p.ownerid
        WHERE i.followers >= 1000 AND i.followers <= 100000
        GROUP BY i.influencerid, i.name, i.username, i.followers, i.profile_pic, i.businesscategoryname
        HAVING COUNT(p.postID) >= 5
        ORDER BY momentum DESC
        LIMIT 10;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        db = get_db()
        results = []
        now = datetime.now(timezone.utc)
        
        for row in rows:
            inf_id, name, username, followers, pic, niche, momentum = row
            
            # Ensure shadow user exists for messaging
            user_doc = await db.users.find_one({"username": username})
            if not user_doc:
                new_user = {
                    "username": username,
                    "email": f"{username}@placeholder.upclout.com",
                    "password": "shadow_user_no_password",
                    "displayName": name,
                    "avatarUrl": pic or "",
                    "userType": "Influencer",
                    "cloutScore": 0,
                    "reviewCount": 0,
                    "is_shadow": True,
                    "createdAt": now,
                    "updatedAt": now
                }
                res = await db.users.insert_one(new_user)
                mongo_id = str(res.inserted_id)
            else:
                mongo_id = str(user_doc["_id"])
                
            results.append({
                "mongo_id": mongo_id,
                "name": name,
                "username": username,
                "followers": followers,
                "profile_pic": pic,
                "niche": niche or "Digital Creator",
                "momentum": round(float(momentum) * 1000, 1) # Scale for a readable "Hot Score"
            })
            
        return results
        
    except Exception as e:
        print("Rising stars error:", e)
        raise HTTPException(status_code=500, detail="Error fetching rising stars")

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
        
        # 2. Top 5 Tagged People (Mentions) - with profile pics
        cur.execute(f"""
            SELECT tu.username, COUNT(*) as count, inf.profile_pic
            FROM taggeduser tu
            JOIN posts_taggeduser ptu ON tu.taggeduserID = ptu.taggeduserID
            JOIN Posts p ON ptu.postID = p.postID
            JOIN {join_table} i ON {join_col}
            LEFT JOIN Influencers inf ON tu.username = inf.username
            WHERE i.username = %s
            GROUP BY tu.username, inf.profile_pic
            ORDER BY count DESC
            LIMIT 6;
        """, (username,))
        mentions = [{"name": row[0], "value": row[1], "pic": row[2]} for row in cur.fetchall()]
        
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
        
        # 4. Post Type Distribution
        cur.execute(f"""
            SELECT type, COUNT(*) as count 
            FROM Posts p 
            JOIN {join_table} i ON {join_col}
            WHERE i.username = %s
            GROUP BY type
        """, (username,))
        post_types = [{"name": row[0], "value": row[1]} for row in cur.fetchall()]

        # 5. Engagement by Hour (Prime Time)
        cur.execute(f"""
            SELECT EXTRACT(HOUR FROM p.timestamp) as hr, AVG(p.likesCount + p.commentsCount)
            FROM Posts p
            JOIN {join_table} i ON {join_col}
            WHERE i.username = %s
            GROUP BY hr ORDER BY hr ASC
        """, (username,))
        hourly = [{"hour": int(row[0]), "engagement": float(row[1])} for row in cur.fetchall()]

        # 6. Caption Keyword Highlights
        cur.execute(f"""
            SELECT caption FROM Posts p
            JOIN {join_table} i ON {join_col}
            WHERE i.username = %s
        """, (username,))
        all_captions = " ".join([row[0] for row in cur.fetchall() if row[0]])
        
        # Simple tokenization & stop word filter
        stop_words = {"the", "and", "is", "of", "to", "in", "a", "with", "for", "on", "it", "this", "my", "your", "are", "at", "be", "was", "has", "have", "you"}
        words = [w.strip("#.,!").lower() for w in all_captions.split() if w.lower().strip("#.,!") not in stop_words and len(w) > 3]
        from collections import Counter
        top_words = [{"name": w, "value": count} for w, count in Counter(words).most_common(12)]

        # 7. Engagement Benchmark
        # Get user avg engagement rate
        cur.execute(f"""
            SELECT i.followers, AVG(p.likesCount + p.commentsCount)
            FROM {join_table} i
            LEFT JOIN Posts p ON {join_col}
            WHERE i.username = %s
            GROUP BY i.followers
        """, (username,))
        bench_row = cur.fetchone()
        user_eng_rate = 0
        if bench_row and bench_row[0] > 0:
            user_eng_rate = (bench_row[1] / bench_row[0]) * 100
        
        benchmark = {
            "user_rate": round(user_eng_rate, 2),
            "avg_rate": 3.5, # industry average for micro influencers
            "status": "Above Average" if user_eng_rate > 3.5 else "Stable"
        }

        # 8. Fetch MongoDB Reviews
        db = get_db()
        # We need the mongo_id for this user. 
        # Since analytics can be for unregistered influencers, we use the shadow/existing user logic.
        user_doc = await db.users.find_one({"username": username})
        reviews = []
        if user_doc:
            reviews_cursor = db.reviews.find({"targetId": user_doc["_id"]}).sort("createdAt", -1).limit(5)
            async for r in reviews_cursor:
                reviews.append({
                    "id": str(r["_id"]),
                    "reviewer": r["reviewerName"],
                    "avatar": r["reviewerAvatar"],
                    "rating": r["rating"],
                    "comment": r["comment"],
                    "date": r["createdAt"].strftime("%b %d") if "createdAt" in r else "Recent"
                })

        cur.close()
        conn.close()
        
        return {
            "hashtags": hashtags,
            "mentions": mentions,
            "trends": trends,
            "post_types": post_types,
            "hourly": hourly,
            "keywords": top_words,
            "benchmark": benchmark,
            "reviews": reviews
        }
        
    except Exception as e:
        print("Analytics error:", e)
        raise HTTPException(status_code=500, detail="Error fetching analytics")
