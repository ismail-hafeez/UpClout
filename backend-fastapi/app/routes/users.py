from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from app.database import get_db
from app.auth import get_current_user
from app.models.review import ReviewRequest

router = APIRouter(prefix="/api/users", tags=["users"])


# ========================
# CONNECTIONS
# ========================

# GET /api/users/connections/requests
@router.get("/connections/requests")
async def get_connection_requests(user: dict = Depends(get_current_user)):
    db = get_db()
    requests = await db.connections.find(
        {"recipient": user["_id"], "status": "pending"}
    ).to_list(length=200)

    result = []
    for req in requests:
        requester = await db.users.find_one(
            {"_id": req["requester"]},
            {"username": 1, "displayName": 1, "avatarUrl": 1, "cloutScore": 1},
        )
        result.append({
            "_id": str(req["_id"]),
            "requester": {
                "_id": str(requester["_id"]),
                "username": requester.get("username", ""),
                "displayName": requester.get("displayName", ""),
                "avatarUrl": requester.get("avatarUrl", ""),
                "cloutScore": requester.get("cloutScore", 0),
            } if requester else None,
            "recipient": str(req["recipient"]),
            "status": req["status"],
            "createdAt": req.get("createdAt"),
            "updatedAt": req.get("updatedAt"),
        })

    return result


# GET /api/users/connections/accepted
@router.get("/connections/accepted")
async def get_accepted_connections(user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = user["_id"]

    connections = await db.connections.find({
        "$or": [{"requester": user_id}, {"recipient": user_id}],
        "status": "accepted",
    }).to_list(length=500)

    friends = []
    for conn in connections:
        # Return the *other* user
        other_id = conn["recipient"] if conn["requester"] == user_id else conn["requester"]
        other = await db.users.find_one(
            {"_id": other_id},
            {"username": 1, "displayName": 1, "avatarUrl": 1, "cloutScore": 1},
        )
        if other:
            friends.append({
                "_id": str(other["_id"]),
                "username": other.get("username", ""),
                "displayName": other.get("displayName", ""),
                "avatarUrl": other.get("avatarUrl", ""),
                "cloutScore": other.get("cloutScore", 0),
            })

    return friends


# POST /api/users/connections/{req_id}/accept
@router.post("/connections/{req_id}/accept")
async def accept_connection(req_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    conn = await db.connections.find_one({"_id": ObjectId(req_id)})
    if not conn:
        raise HTTPException(status_code=404, detail="Request not found")
    if conn["recipient"] != user["_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    now = datetime.now(timezone.utc)
    await db.connections.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"status": "accepted", "updatedAt": now}},
    )

    conn["status"] = "accepted"
    conn["_id"] = str(conn["_id"])
    conn["requester"] = str(conn["requester"])
    conn["recipient"] = str(conn["recipient"])
    return conn


# POST /api/users/connections/{req_id}/reject
@router.post("/connections/{req_id}/reject")
async def reject_connection(req_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    conn = await db.connections.find_one({"_id": ObjectId(req_id)})
    if not conn:
        raise HTTPException(status_code=404, detail="Request not found")
    if conn["recipient"] != user["_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    await db.connections.delete_one({"_id": ObjectId(req_id)})
    return {"message": "Rejected"}


# DELETE /api/users/connections/{req_id}
@router.delete("/connections/{req_id}")
async def delete_connection(req_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    conn = await db.connections.find_one({"_id": ObjectId(req_id)})
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    if conn["recipient"] != user["_id"] and conn["requester"] != user["_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    await db.connections.delete_one({"_id": ObjectId(req_id)})
    return {"message": "Connection removed"}


# GET /api/users/{user_id}/connection-status
@router.get("/{user_id}/connection-status")
async def connection_status(user_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    me = str(user["_id"])
    if user_id == me:
        return {"status": "self"}

    target_oid = ObjectId(user_id)
    conn = await db.connections.find_one({
        "$or": [
            {"requester": user["_id"], "recipient": target_oid},
            {"requester": target_oid, "recipient": user["_id"]},
        ]
    })

    if not conn:
        return {"status": "none"}

    return {
        "status": conn["status"],
        "isRequester": conn["requester"] == user["_id"],
        "connectionId": str(conn["_id"]),
    }


# POST /api/users/{user_id}/connect
@router.post("/{user_id}/connect")
async def send_connection_request(user_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    me = user["_id"]
    if user_id == str(me):
        raise HTTPException(status_code=400, detail="Cannot connect to self")

    target_oid = ObjectId(user_id)
    existing = await db.connections.find_one({
        "$or": [
            {"requester": me, "recipient": target_oid},
            {"requester": target_oid, "recipient": me},
        ]
    })

    if existing:
        # If the other person sent a request to us, auto-accept
        if existing["status"] == "pending" and existing["recipient"] == me:
            await db.connections.update_one(
                {"_id": existing["_id"]},
                {"$set": {"status": "accepted", "updatedAt": datetime.now(timezone.utc)}},
            )
            return {"status": "accepted"}
        return {"status": existing["status"]}

    now = datetime.now(timezone.utc)
    doc = {
        "requester": me,
        "recipient": target_oid,
        "status": "pending",
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.connections.insert_one(doc)
    return {"status": "pending", "connectionId": str(result.inserted_id)}


# ========================
# USERS & REVIEWS
# ========================

# GET /api/users/{user_id}
@router.get("/{user_id}")
async def get_user_profile(user_id: str):
    db = get_db()
    try:
        user = await db.users.find_one(
            {"_id": ObjectId(user_id)},
            {"_id": 1, "username": 1, "displayName": 1, "avatarUrl": 1, "cloutScore": 1, "reviewCount": 1, "createdAt": 1},
        )
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])
    return user


# GET /api/users/{user_id}/reviews
@router.get("/{user_id}/reviews")
async def get_reviews(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_db()
    target_oid = ObjectId(user_id)
    skip = (page - 1) * limit

    reviews_cursor = db.reviews.find(
        {"targetUser": target_oid}
    ).sort("createdAt", -1).skip(skip).limit(limit)
    reviews = await reviews_cursor.to_list(length=limit)

    total = await db.reviews.count_documents({"targetUser": target_oid})

    result = []
    for rev in reviews:
        reviewer = await db.users.find_one(
            {"_id": rev["reviewer"]},
            {"username": 1, "displayName": 1, "avatarUrl": 1},
        )
        result.append({
            "_id": str(rev["_id"]),
            "reviewer": {
                "_id": str(reviewer["_id"]),
                "username": reviewer.get("username", ""),
                "displayName": reviewer.get("displayName", ""),
                "avatarUrl": reviewer.get("avatarUrl", ""),
            } if reviewer else None,
            "targetUser": str(rev["targetUser"]),
            "rating": rev.get("rating"),
            "comment": rev.get("comment", ""),
            "createdAt": rev.get("createdAt"),
            "updatedAt": rev.get("updatedAt"),
        })

    return {
        "reviews": result,
        "total": total,
        "page": page,
        "totalPages": max(1, -(-total // limit)),  # ceil division
    }


# POST /api/users/{user_id}/reviews
@router.post("/{user_id}/reviews")
async def submit_review(user_id: str, body: ReviewRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    target_oid = ObjectId(user_id)
    me = user["_id"]

    if user_id == str(me):
        raise HTTPException(status_code=400, detail="You cannot review yourself.")

    if not body.rating or body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    # Verify connection
    conn = await db.connections.find_one({
        "$or": [
            {"requester": me, "recipient": target_oid},
            {"requester": target_oid, "recipient": me},
        ],
        "status": "accepted",
    })
    if not conn:
        raise HTTPException(status_code=403, detail="You must be connected to leave a review.")

    now = datetime.now(timezone.utc)
    # Upsert review
    await db.reviews.update_one(
        {"reviewer": me, "targetUser": target_oid},
        {"$set": {"rating": body.rating, "comment": body.comment or "", "updatedAt": now},
         "$setOnInsert": {"createdAt": now}},
        upsert=True,
    )

    # Recalculate average rating
    pipeline = [
        {"$match": {"targetUser": target_oid}},
        {"$group": {
            "_id": "$targetUser",
            "averageRating": {"$avg": "$rating"},
            "numOfReviews": {"$sum": 1},
        }},
    ]
    stats = await db.reviews.aggregate(pipeline).to_list(length=1)

    clout_score = round(stats[0]["averageRating"], 1) if stats else 0
    review_count = stats[0]["numOfReviews"] if stats else 0

    await db.users.update_one(
        {"_id": target_oid},
        {"$set": {"cloutScore": clout_score, "reviewCount": review_count}},
    )

    return {"message": "Review submitted successfully", "cloutScore": clout_score, "reviewCount": review_count}
