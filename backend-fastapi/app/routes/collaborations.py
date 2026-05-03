from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from app.database import get_db
from app.auth import get_current_user
from app.models.collaboration import (
    CollaborationCreateRequest,
    CollaborationStatusRequest,
    CollaborationDeliverablesRequest,
    CollaborationPaymentRequest,
)

router = APIRouter(prefix="/api/collaborations", tags=["collaborations"])


def _serialize_collab(collab: dict) -> dict:
    """Serialize a collaboration document, converting ObjectIds to strings."""
    result = dict(collab)
    result["_id"] = str(result["_id"])
    if "campaignId" in result and isinstance(result["campaignId"], ObjectId):
        result["campaignId"] = str(result["campaignId"])
    if "influencerId" in result and isinstance(result["influencerId"], ObjectId):
        result["influencerId"] = str(result["influencerId"])
    if "brandId" in result and isinstance(result["brandId"], ObjectId):
        result["brandId"] = str(result["brandId"])
    return result


async def _populate_collab(db, collab: dict) -> dict:
    """Populate campaign, brand, and influencer references."""
    result = dict(collab)
    result["_id"] = str(result["_id"])

    # Populate campaignId
    if result.get("campaignId"):
        cid = result["campaignId"] if isinstance(result["campaignId"], ObjectId) else ObjectId(result["campaignId"])
        campaign = await db.campaigns.find_one({"_id": cid})
        if campaign:
            campaign["_id"] = str(campaign["_id"])
            if "brandId" in campaign:
                campaign["brandId"] = str(campaign["brandId"])
            result["campaignId"] = campaign
        else:
            result["campaignId"] = str(result["campaignId"])

    # Populate brandId
    if result.get("brandId"):
        bid = result["brandId"] if isinstance(result["brandId"], ObjectId) else ObjectId(result["brandId"])
        brand = await db.users.find_one(
            {"_id": bid},
            {"username": 1, "displayName": 1, "avatarUrl": 1, "userType": 1},
        )
        if brand:
            from app.auth import get_pg_profile_pic
            pg_pic = get_pg_profile_pic(brand.get("username", ""), brand.get("userType", "Brand"))
            brand["_id"] = str(brand["_id"])
            if pg_pic:
                brand["avatarUrl"] = pg_pic
            result["brandId"] = brand
        else:
            result["brandId"] = str(result["brandId"])

    # Populate influencerId
    if result.get("influencerId"):
        iid = result["influencerId"] if isinstance(result["influencerId"], ObjectId) else ObjectId(result["influencerId"])
        influencer = await db.users.find_one(
            {"_id": iid},
            {"username": 1, "displayName": 1, "avatarUrl": 1, "userType": 1},
        )
        if influencer:
            from app.auth import get_pg_profile_pic
            pg_pic = get_pg_profile_pic(influencer.get("username", ""), influencer.get("userType", "Influencer"))
            influencer["_id"] = str(influencer["_id"])
            if pg_pic:
                influencer["avatarUrl"] = pg_pic
            result["influencerId"] = influencer
        else:
            result["influencerId"] = str(result["influencerId"])

    return result


# POST /api/collaborations
@router.post("", status_code=201)
async def create_collaboration(body: CollaborationCreateRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    campaign_oid = ObjectId(body.campaignId)
    
    # Handle influencer ID which might be from PG database (not registered)
    influencer_id_str = str(body.influencerId)
    if influencer_id_str.startswith("pg_inf_"):
        # This user was found in PG but might not be in MongoDB yet
        # We search them by username if we can find it
        # Actually, let's just use the ID as provided from the frontend
        # The frontend search for pg_inf_ results includes username.
        # Since the backend create_collaboration only gets influencerId, we might need a workaround.
        
        # IMPROVEMENT: Re-fetch the user details from PG if this is a PG ID
        import psycopg2
        pg_id = influencer_id_str.replace("pg_inf_", "")
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        cur.execute("SELECT username, name, profile_pic FROM influencers WHERE influencerid = %s", (pg_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="PG Influencer not found")
            
        username = row[0]
        display_name = row[1] or row[0]
        avatar_url = row[2] or ""
        
        # Check if already in MongoDB
        user_doc = await db.users.find_one({"username": username})
        if not user_doc:
            # Create a "placeholder" or shadow user in MongoDB
            now = datetime.now(timezone.utc)
            user_doc = {
                "username": username,
                "email": f"{username}@placeholder.upclout.com", # placeholder email
                "password": "shadow_user_no_password",
                "displayName": display_name,
                "avatarUrl": avatar_url,
                "userType": "Influencer",
                "cloutScore": 0,
                "reviewCount": 0,
                "is_shadow": True, # Mark as shadow user
                "createdAt": now,
                "updatedAt": now
            }
            res = await db.users.insert_one(user_doc)
            user_doc["_id"] = res.inserted_id
            
        influencer_oid = user_doc["_id"]
    else:
        # Standard MongoDB ObjectId
        influencer_oid = ObjectId(body.influencerId)

    existing = await db.collaborations.find_one({
        "campaignId": campaign_oid,
        "influencerId": influencer_oid,
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Collaboration already exists for this influencer and campaign.",
        )

    now = datetime.now(timezone.utc)
    doc = {
        "campaignId": campaign_oid,
        "influencerId": influencer_oid,
        "brandId": user["_id"],
        "deliverables": [d.model_dump() for d in (body.deliverables or [])],
        "paymentDetails": {
            "amount": body.paymentAmount,
            "currency": body.currency or "USD",
            "status": "Pending",
        },
        "status": "Invited",
        "isNew": True,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.collaborations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_collab(doc)


# PUT /api/collaborations/mark-seen
@router.put("/mark-seen")
async def mark_seen(user: dict = Depends(get_current_user)):
    db = get_db()
    await db.collaborations.update_many(
        {"influencerId": user["_id"], "isNew": {"$ne": False}},
        {"$set": {"isNew": False}},
    )
    return {"success": True}


# GET /api/collaborations
@router.get("")
async def list_collaborations(user: dict = Depends(get_current_user)):
    db = get_db()
    collabs = await db.collaborations.find({
        "$or": [{"brandId": user["_id"]}, {"influencerId": user["_id"]}]
    }).sort("createdAt", -1).to_list(length=500)

    result = []
    for c in collabs:
        result.append(await _populate_collab(db, c))

    return result


# GET /api/collaborations/user/{user_id}
@router.get("/user/{user_id}")
async def get_public_collaborations(user_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    # Only allow the user themselves
    if str(user["_id"]) != user_id:
        return []

    target_oid = ObjectId(user_id)
    collabs = await db.collaborations.find({
        "$or": [{"brandId": target_oid}, {"influencerId": target_oid}]
    }).sort("createdAt", -1).to_list(length=500)

    result = []
    for c in collabs:
        populated = await _populate_collab(db, c)
        # For public view, campaign only needs title
        if isinstance(populated.get("campaignId"), dict):
            populated["campaignId"] = {
                "_id": populated["campaignId"].get("_id"),
                "title": populated["campaignId"].get("title", ""),
            }
        result.append(populated)

    return result


# PUT /api/collaborations/{collab_id}/status
@router.put("/{collab_id}/status")
async def update_status(
    collab_id: str,
    body: CollaborationStatusRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    collab = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    if not collab:
        raise HTTPException(status_code=404, detail="Not found")

    # If an influencer accepts an 'Invited' collaboration, move it to 'Negotiating'
    new_status = body.status
    if collab.get("status") == "Invited" and body.status == "Content Creation":
        # The user wanted Accepting to move to "Negotiating phase"
        new_status = "Negotiating"

    await db.collaborations.update_one(
        {"_id": ObjectId(collab_id)},
        {"$set": {"status": new_status, "updatedAt": datetime.now(timezone.utc)}},
    )
    
    # NEW: Automatically create conversation on acceptance
    if new_status == "Negotiating":
        try:
            # Get campaign and brand info
            brand_id = collab.get("brandId")
            influencer_id = collab.get("influencerId")
            campaign_id = collab.get("campaignId")
            
            # Check if conversation already exists
            existing_conv = await db.conversations.find_one({
                "participants": {"$all": [brand_id, influencer_id], "$size": 2}
            })
            
            if not existing_conv:
                now = datetime.now(timezone.utc)
                conv_doc = {
                    "participants": [brand_id, influencer_id],
                    "lastMessage": None,
                    "lastMessageAt": now,
                    "unreadCounts": {},
                    "campaignId": campaign_id, # Link to campaign
                    "createdAt": now,
                    "updatedAt": now,
                }
                await db.conversations.insert_one(conv_doc)
            else:
                # Update existing conversation with campaign context if not set
                if not existing_conv.get("campaignId"):
                    await db.conversations.update_one(
                        {"_id": existing_conv["_id"]},
                        {"$set": {"campaignId": campaign_id}}
                    )
        except Exception as e:
            print("Auto-chat creation error:", e)

    updated = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    return _serialize_collab(updated)


# DELETE /api/collaborations/{collab_id}/reject
@router.delete("/{collab_id}/reject")
async def reject_collaboration(
    collab_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    collab = await db.collaborations.find_one({
        "_id": ObjectId(collab_id),
        "influencerId": user["_id"]
    })
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration not found or unauthorized")

    await db.collaborations.update_one(
        {"_id": ObjectId(collab_id)},
        {"$set": {"status": "Declined", "updatedAt": datetime.now(timezone.utc)}}
    )
    return {"success": True, "message": "Collaboration invitation declined"}


# PUT /api/collaborations/{collab_id}/deliverables
@router.put("/{collab_id}/deliverables")
async def update_deliverables(
    collab_id: str,
    body: CollaborationDeliverablesRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    collab = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    if not collab:
        raise HTTPException(status_code=404, detail="Not found")

    deliverables = [d.model_dump() for d in body.deliverables]
    await db.collaborations.update_one(
        {"_id": ObjectId(collab_id)},
        {"$set": {"deliverables": deliverables, "updatedAt": datetime.now(timezone.utc)}},
    )
    updated = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    return _serialize_collab(updated)


# PUT /api/collaborations/{collab_id}/payment
@router.put("/{collab_id}/payment")
async def update_payment(
    collab_id: str,
    body: CollaborationPaymentRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    collab = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    if not collab:
        raise HTTPException(status_code=404, detail="Not found")

    update_doc = {"paymentDetails.status": body.status, "updatedAt": datetime.now(timezone.utc)}
    if body.amount is not None:
        update_doc["paymentDetails.amount"] = body.amount

    await db.collaborations.update_one(
        {"_id": ObjectId(collab_id)},
        {"$set": update_doc},
    )
    updated = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    return _serialize_collab(updated)

# POST /api/collaborations/{collab_id}/review
@router.post("/{collab_id}/review")
async def submit_review(
    collab_id: str,
    rating: int, # 1-5
    comment: str,
    user: dict = Depends(get_current_user)
):
    db = get_db()
    collab = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    if not collab:
        raise HTTPException(status_code=404, detail="Collab not found")
    
    if collab.status != "Completed":
        raise HTTPException(status_code=400, detail="Cannot review an incomplete collaboration")

    is_brand = user["userType"] == "Brand"
    reviewer_id = ObjectId(user["_id"])
    
    # Determine target of review
    if is_brand:
        target_id = ObjectId(collab["influencerId"])
    else:
        target_id = ObjectId(collab["brandId"])

    # Check if review already exists for this side
    existing = await db.reviews.find_one({"collabId": ObjectId(collab_id), "reviewerId": reviewer_id})
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this collaboration")

    review_doc = {
        "collabId": ObjectId(collab_id),
        "reviewerId": reviewer_id,
        "reviewerName": user.get("displayName") or user.get("username"),
        "reviewerAvatar": user.get("avatarUrl"),
        "targetId": target_id,
        "rating": min(5, max(1, rating)),
        "comment": comment,
        "createdAt": datetime.now(timezone.utc)
    }

    await db.reviews.insert_one(review_doc)

    # Update target user average rating (simplistic logic)
    target_user = await db.users.find_one({"_id": target_id})
    if target_user:
        current_rating = target_user.get("cloutScore") or 0
        current_count = target_user.get("reviewCount") or 0
        new_count = current_count + 1
        new_rating = ((current_rating * current_count) + rating) / new_count
        
        await db.users.update_one(
            {"_id": target_id},
            {"$set": {"cloutScore": round(new_rating, 1), "reviewCount": new_count}}
        )

    return {"success": True, "rating": rating}