from fastapi import APIRouter, HTTPException, Depends
from app.auth import get_current_user
from app.database import get_db
from app.chatbot import llm
import psycopg2
from typing import Optional

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

def get_db_connection():
    return psycopg2.connect(database="postgres", user="postgres", password=1040)

@router.get("/{username}")
async def get_profile_details(username: str, user: dict = Depends(get_current_user)):
    """Fetches comprehensive profile details, stats, highest liked post, and AI summary."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Identify User Type and Fetch Basic Info
        # Check Influencers first
        cur.execute("""
            SELECT influencerid, name, username, followers, following, postcount, bio, profile_pic, businesscategoryname, location
            FROM Influencers WHERE username = %s
        """, (username,))
        result = cur.fetchone()
        user_type = "Influencer"
        
        if not result:
            # Check Brands
            cur.execute("""
                SELECT brandid, name, username, followers, following, postcount, bio, profile_pic, businesscategoryname, location
                FROM Brands WHERE username = %s
            """, (username,))
            result = cur.fetchone()
            user_type = "Brand"
            
        if not result:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Profile not found in UpClout database")
            
        profile_id, name, uname, followers, following, posts, bio, pic, niche, loc = result
        
        # 2. Fetch Highest Liked Post
        owner_col = "ownerid" if user_type == "Influencer" else "ownerbrandid"
        cur.execute(f"""
            SELECT postID, type, caption, url, likesCount, commentsCount, timestamp
            FROM Posts WHERE {owner_col} = %s
            ORDER BY likesCount DESC LIMIT 1
        """, (profile_id,))
        top_post_raw = cur.fetchone()
        top_post = None
        if top_post_raw:
            top_post = {
                "id": top_post_raw[0],
                "type": top_post_raw[1],
                "caption": top_post_raw[2],
                "url": top_post_raw[3],
                "likes": top_post_raw[4],
                "comments": top_post_raw[5],
                "date": top_post_raw[6].strftime("%b %d, %Y") if top_post_raw[6] else None
            }
            
        # 3. Calculate Engagement Rate (Avg of last 10 posts)
        cur.execute(f"""
            SELECT AVG(likesCount + commentsCount) 
            FROM (SELECT likesCount, commentsCount FROM Posts WHERE {owner_col} = %s ORDER BY timestamp DESC LIMIT 10) as last_posts
        """, (profile_id,))
        avg_eng = cur.fetchone()[0] or 0
        eng_rate = (avg_eng / followers * 100) if followers > 0 else 0
        
        # 4. Fetch Top Hashtags for AI Summary
        cur.execute(f"""
            SELECT h.tag_name, COUNT(*) as count 
            FROM Hashtags h
            JOIN posts_hashtags ph ON h.hashtagid = ph.hashtag_id
            JOIN Posts p ON ph.post_id = p.postID
            WHERE p.{owner_col} = %s
            GROUP BY h.tag_name ORDER BY count DESC LIMIT 5
        """, (profile_id,))
        hashtags = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        # 5. Check/Create MongoDB Shadow User for Messaging
        db = get_db()
        user_doc = await db.users.find_one({"username": uname})
        if not user_doc:
            # Create shadow user if they don't exist in MongoDB yet
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            new_user = {
                "username": uname,
                "email": f"{uname}@placeholder.upclout.com",
                "password": "shadow_user_no_password",
                "displayName": name,
                "avatarUrl": pic or "",
                "userType": user_type,
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

        # 6. Generate AI Summary (Owly)
        summary_prompt = f"""
        Summarize this Instagram {user_type} in 2-3 concise sentences for a brand looking to collaborate.
        Name: {name} (@{uname})
        Bio: {bio}
        Niche: {niche}
        Top Hashtags: {', '.join(hashtags)}
        
        Focus on their content style and value proposition. Start with a "Hoot!" or "Wise choice".
        """
        
        try:
            ai_response = await llm.ainvoke(summary_prompt)
            summary = ai_response.content
        except:
            summary = f"{name} is a {niche} {user_type.lower()} with a focus on {', '.join(hashtags[:2])}. They have a strong following of {followers:,}."

        return {
            "mongo_id": mongo_id,
            "type": user_type,
            "name": name,
            "username": uname,
            "followers": followers,
            "following": following,
            "posts": posts,
            "bio": bio,
            "profile_pic": pic,
            "niche": niche or "Digital Creator",
            "location": loc or "Global",
            "eng_rate": round(eng_rate, 2),
            "top_post": top_post,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print("Profile Error:", e)
        raise HTTPException(status_code=500, detail="Internal server error fetching profile")
