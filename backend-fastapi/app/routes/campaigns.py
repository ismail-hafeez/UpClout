from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from app.database import get_db
from app.auth import get_current_user
from app.models.campaign import CampaignCreateRequest, CampaignStatusRequest

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


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
    doc["_id"] = str(result.inserted_id)
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
