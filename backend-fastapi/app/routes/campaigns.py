from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from app.database import get_db
from app.auth import get_current_user
from app.models.campaign import CampaignCreateRequest, CampaignStatusRequest

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


import psycopg2
from bson import ObjectId

# POST /api/campaigns
@router.post("", status_code=201)
async def create_campaign(body: CampaignCreateRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        "title": body.title,
        "goal": body.goal,
        "budget": body.budget,
        "niche": body.niche or "",
        "timeline": body.timeline or "",
        "brandId": user["_id"],
        "status": "Active",
        "startDate": now,
        "completionDate": None,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.campaigns.insert_one(doc)
    campaign_id = result.inserted_id
    
    # Auto-invite recommended influencers
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()
        
        # Get recommended influencers for this brand
        query = """
        SELECT i.username
        FROM brand_recommendations br
        JOIN influencers i ON br.recommended_influencer_id = i.influencerid
        WHERE br.brand_id = (SELECT brandid FROM brands WHERE username = %s LIMIT 1);
        """
        cur.execute(query, (user.get("username"),))
        rec_rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if rec_rows:
            rec_usernames = [row[0] for row in rec_rows]
            
            # Find these influencers in our MongoDB users collection
            influencers = await db.users.find({
                "username": {"$in": rec_usernames},
                "userType": "Influencer"
            }).to_list(length=100)
            
            # Create a collaboration invite for each registered influencer
            collab_docs = []
            for inf in influencers:
                collab_docs.append({
                    "campaignId": campaign_id,
                    "influencerId": inf["_id"],
                    "brandId": user["_id"],
                    "deliverables": [], # Initial empty deliverables
                    "paymentDetails": {
                        "amount": 0, # Start at 0, negotiate later
                        "currency": "PKR",
                        "status": "Pending",
                    },
                    "status": "Invited",
                    "isNew": True,
                    "createdAt": now,
                    "updatedAt": now,
                })
            
            if collab_docs:
                await db.collaborations.insert_many(collab_docs)
                
    except Exception as e:
        print("Campaign creation auto-invite error:", e)

    doc["_id"] = str(campaign_id)
    doc["brandId"] = str(doc["brandId"])
    return doc


# GET /api/campaigns
@router.get("")
async def list_campaigns(user: dict = Depends(get_current_user)):
    db = get_db()
    campaigns = await db.campaigns.find(
        {"brandId": user["_id"]}
    ).sort("createdAt", -1).to_list(length=200)

    for c in campaigns:
        c["_id"] = str(c["_id"])
        c["brandId"] = str(c["brandId"])

    return campaigns


# PUT /api/campaigns/{campaign_id}/status
@router.put("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    body: CampaignStatusRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    campaign = await db.campaigns.find_one({
        "_id": ObjectId(campaign_id),
        "brandId": user["_id"],
    })
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    updates = {"status": body.status, "updatedAt": datetime.now(timezone.utc)}

    if body.status == "Completed":
        updates["completionDate"] = datetime.now(timezone.utc)
        # Also mark all collaborations for this campaign as Completed
        await db.collaborations.update_many(
            {"campaignId": ObjectId(campaign_id)},
            {"$set": {"status": "Completed"}},
        )

    await db.campaigns.update_one({"_id": ObjectId(campaign_id)}, {"$set": updates})

    updated = await db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    updated["_id"] = str(updated["_id"])
    updated["brandId"] = str(updated["brandId"])
    return updated