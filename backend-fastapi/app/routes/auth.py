import os
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from bson import ObjectId
from app.database import get_db
from app.auth import (
    hash_password,
    verify_password,
    create_token,
    user_to_safe,
    get_current_user,
    verify_brand
)
from app.models.user import RegisterRequest, LoginRequest, ProfileUpdateRequest
import psycopg2

router = APIRouter(prefix="/api/auth", tags=["auth"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# POST /api/auth/register
@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    db = get_db()

    if not body.username or not body.email or not body.password:
        raise HTTPException(status_code=400, detail="Username, email and password are required")

    # Check for existing user
    existing = await db.users.find_one(
        {"$or": [{"email": body.email.lower()}, {"username": body.username}]}
    )
    
    # Shadow User Claiming Logic
    is_claiming_shadow = False
    if existing:
        # If it's a shadow user matching ONLY the username, we can claim it
        if existing.get("username") == body.username and existing.get("is_shadow") == True:
            # Check if the NEW email is already used by someone else (not a shadow)
            email_exists = await db.users.find_one({"email": body.email.lower(), "username": {"$ne": body.username}})
            if email_exists:
                raise HTTPException(status_code=409, detail="Email already in use")
            is_claiming_shadow = True
        else:
            field = "Email" if existing.get("email") == body.email.lower() else "Username"
            raise HTTPException(status_code=409, detail=f"{field} already in use")

    now = datetime.now(timezone.utc)
    user_doc = {
        "username": body.username.strip(),
        "email": body.email.lower().strip(),
        "password": hash_password(body.password),
        "displayName": (body.displayName or "").strip(),
        "instagramId": None,
        "instagramHandle": None,
        "instagramAccessToken": None,
        "cloutScore": 0,
        "reviewCount": 0,
        "userType": body.userType if body.userType in ("Influencer", "Brand") else "Influencer",
        "is_shadow": False, # Explicitly untag shadow
        "updatedAt": now,
    }

    if is_claiming_shadow:
        # Update existing record
        await db.users.update_one({"_id": existing["_id"]}, {"$set": user_doc})
        user_doc["_id"] = existing["_id"]
        user_doc["createdAt"] = existing.get("createdAt", now)
    else:
        # Create new record
        user_doc["avatarUrl"] = ""
        user_doc["createdAt"] = now
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

    token = create_token(str(user_doc["_id"]))
    return {"token": token, "user": user_to_safe(user_doc)}


# POST /api/auth/login
@router.post("/login")
async def login(body: LoginRequest):
    db = get_db()

    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    # Allow login with username or email
    user = await db.users.find_one(
        {"$or": [{"username": body.username}, {"email": body.username}]}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(str(user["_id"]))
    return {"token": token, "user": user_to_safe(user)}


# GET /api/auth/me
@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": user_to_safe(user)}


# PATCH /api/auth/profile
@router.patch("/profile")
async def update_profile(body: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    updates = {}
    if body.displayName is not None:
        updates["displayName"] = body.displayName.strip()
    if body.avatarUrl is not None:
        updates["avatarUrl"] = body.avatarUrl.strip()

    if updates:
        updates["updatedAt"] = datetime.now(timezone.utc)
        await db.users.update_one({"_id": user["_id"]}, {"$set": updates})

    updated_user = await db.users.find_one({"_id": user["_id"]})
    return {"user": user_to_safe(updated_user)}


# GET /api/auth/brand-stats
@router.get("/brand-stats")
async def get_brand_stats(user: dict = Depends(get_current_user)):
    user_type = user.get("userType")
    if user_type not in ("Brand", "Influencer"):
        return {}

    table = "brands" if user_type == "Brand" else "influencers"
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        cur.execute(f"SELECT followers, following, postcount, profile_pic, businesscategoryname, location FROM {table} WHERE username = %s LIMIT 1", (user.get("username"),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                "followers": row[0], 
                "following": row[1], 
                "posts": row[2], 
                "profile_pic": row[3],
                "niche": row[4],
                "location": row[5]
            }
    except Exception as e:
        print(f"PG {table} stats error:", e)
    return {}


# GET /api/auth/recommendations
@router.get("/recommendations")
async def get_recommendations(user: dict = Depends(get_current_user)):
    user_type = user.get("userType")
    if user_type not in ("Brand", "Influencer"):
        return []

    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        
        if user_type == "Brand":
            query = """
            SELECT i.influencerid, i.name, i.username, i.followers, i.businesscategoryname, i.profile_pic
            FROM brand_recommendations br
            JOIN influencers i ON br.recommended_influencer_id = i.influencerid
            WHERE br.brand_id = (SELECT brandid FROM brands WHERE username = %s LIMIT 1);
            """
        else:
            query = """
            SELECT b.brandid, b.name, b.username, b.followers, b.businesscategoryname, b.profile_pic
            FROM influencer_recommendations ir
            JOIN brands b ON ir.recommended_brand_id = b.brandid
            WHERE ir.influencer_id = (SELECT influencerid FROM influencers WHERE username = %s LIMIT 1);
            """
            
        cur.execute(query, (user.get("username"),))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        recommendations = []
        for row in rows:
            # Connect the columns based on the query:
            # 0: influencerid, 1: name, 2: username, 3: followers, 4: businesscategoryname, 5: profile_pic
            f_count = row[3]
            try:
                f_count_val = int(f_count) if f_count else 0
            except:
                f_count_val = 0
                
            if f_count_val >= 1000000:
                f_str = f"{f_count_val/1000000:.1f}M"
            elif f_count_val >= 1000:
                f_str = f"{f_count_val/1000:.1f}K"
            else:
                f_str = str(f_count_val)
                
            # Randomize clout based on followers or just pick a good score
            clout_score = 85
            if f_count_val > 500000: clout_score = 95
            elif f_count_val > 100000: clout_score = 92
            elif f_count_val > 10000: clout_score = 88
            
            recommendations.append({
                "id": str(row[0]),
                "name": row[1] if row[1] else row[2],
                "handle": f"@{row[2]}",
                "clout": clout_score,
                "followers": f_str,
                "niche": row[4] or "Lifestyle",
                "profile_pic": row[5]
            })
            
        return recommendations
    except Exception as e:
        print("PG recommendations error:", e)
    return []


# GET /api/auth/search-pg
@router.get("/search-pg")
async def search_pg(
    q: str = Query(""),
    user: dict = Depends(get_current_user),
):
    if not q or len(q) < 2:
        return []
        
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        search_term = f"%{q}%"
        
        # Search Influencers
        cur.execute("""
            SELECT influencerid, name, username, businesscategoryname, profile_pic, followers
            FROM influencers 
            WHERE username ILIKE %s OR name ILIKE %s
            LIMIT 10
        """, (search_term, search_term))
        inf_rows = cur.fetchall()
        
        # Search Brands
        cur.execute("""
            SELECT brandid, name, username, businesscategoryname, profile_pic, followers
            FROM brands 
            WHERE username ILIKE %s OR name ILIKE %s
            LIMIT 10
        """, (search_term, search_term))
        brand_rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        results = []
        
        # Process Influencers
        for row in inf_rows:
            results.append({
                "_id": f"pg_inf_{row[0]}",
                "username": row[2] if row[2] else "",
                "displayName": row[1] if row[1] else row[2],
                "avatarUrl": row[4] if row[4] else None,
                "niche": row[3],
                "followers": row[5],
                "userType": "Influencer",
                "is_pg": True
            })
            
        # Process Brands
        for row in brand_rows:
            results.append({
                "_id": f"pg_brand_{row[0]}",
                "username": row[2] if row[2] else "",
                "displayName": row[1] if row[1] else row[2],
                "avatarUrl": row[4] if row[4] else None,
                "niche": row[3],
                "followers": row[5],
                "userType": "Brand",
                "is_pg": True
            })
            
        return results
    except Exception as e:
        print("PG search error:", e)
    return []


# POST /api/auth/avatar
@router.post("/avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    db = get_db()

    if not avatar.content_type or not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    # 5MB limit
    contents = await avatar.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    ext = os.path.splitext(avatar.filename or ".png")[1]
    filename = f"avatar-{str(user['_id'])}-{int(datetime.now(timezone.utc).timestamp() * 1000)}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    avatar_url = f"/uploads/{filename}"
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"avatarUrl": avatar_url, "updatedAt": datetime.now(timezone.utc)}},
    )

    updated_user = await db.users.find_one({"_id": user["_id"]})
    return {"user": user_to_safe(updated_user)}