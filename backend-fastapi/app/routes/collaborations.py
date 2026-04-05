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
            {"username": 1, "displayName": 1, "avatarUrl": 1},
        )
        if brand:
            brand["_id"] = str(brand["_id"])
            result["brandId"] = brand
        else:
            result["brandId"] = str(result["brandId"])

    # Populate influencerId
    if result.get("influencerId"):
        iid = result["influencerId"] if isinstance(result["influencerId"], ObjectId) else ObjectId(result["influencerId"])
        influencer = await db.users.find_one(
            {"_id": iid},
            {"username": 1, "displayName": 1, "avatarUrl": 1},
        )
        if influencer:
            influencer["_id"] = str(influencer["_id"])
            result["influencerId"] = influencer
        else:
            result["influencerId"] = str(result["influencerId"])

    return result


# POST /api/collaborations
@router.post("", status_code=201)
async def create_collaboration(body: CollaborationCreateRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    campaign_oid = ObjectId(body.campaignId)
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
        "status": "Negotiating",
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

    await db.collaborations.update_one(
        {"_id": ObjectId(collab_id)},
        {"$set": {"status": body.status, "updatedAt": datetime.now(timezone.utc)}},
    )
    updated = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    return _serialize_collab(updated)


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

    await db.collaborations.update_one(
        {"_id": ObjectId(collab_id)},
        {"$set": {"paymentDetails.status": body.status, "updatedAt": datetime.now(timezone.utc)}},
    )
    updated = await db.collaborations.find_one({"_id": ObjectId(collab_id)})
    return _serialize_collab(updated)
