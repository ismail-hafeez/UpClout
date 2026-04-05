import os
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from bson import ObjectId
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _serialize_message(msg: dict) -> dict:
    """Serialize a message document for JSON response."""
    result = {
        "_id": str(msg["_id"]),
        "conversationId": str(msg["conversationId"]),
        "text": msg.get("text", ""),
        "createdAt": msg.get("createdAt", ""),
        "updatedAt": msg.get("updatedAt", ""),
        "readBy": [str(r) for r in msg.get("readBy", [])],
    }
    if "sender" in msg and isinstance(msg["sender"], dict):
        result["sender"] = {
            "_id": str(msg["sender"]["_id"]),
            "username": msg["sender"].get("username", ""),
            "displayName": msg["sender"].get("displayName", ""),
            "avatarUrl": msg["sender"].get("avatarUrl", ""),
        }
    elif "sender" in msg:
        result["sender"] = str(msg["sender"])

    if msg.get("file"):
        result["file"] = msg["file"]

    return result


async def _populate_user(db, user_id, fields=None):
    """Fetch a user by ID and return selected fields."""
    if fields is None:
        fields = {"username": 1, "displayName": 1, "avatarUrl": 1}
    user = await db.users.find_one({"_id": ObjectId(user_id) if isinstance(user_id, str) else user_id}, fields)
    if user:
        user["_id"] = str(user["_id"])
    return user


# GET /api/conversations
@router.get("")
async def list_conversations(user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = user["_id"]

    conversations = await db.conversations.find(
        {"participants": user_id}
    ).sort("lastMessageAt", -1).to_list(length=200)

    result = []
    for conv in conversations:
        # Find the other participant
        other_id = None
        for p in conv.get("participants", []):
            if p != user_id:
                other_id = p
                break

        other_user = await _populate_user(db, other_id) if other_id else None

        # Get last message text
        last_msg_text = ""
        if conv.get("lastMessage"):
            last_msg = await db.messages.find_one({"_id": conv["lastMessage"]})
            if last_msg:
                last_msg_text = last_msg.get("text", "")

        unread_counts = conv.get("unreadCounts", {})
        unread = unread_counts.get(str(user_id), 0)

        result.append({
            "id": str(conv["_id"]),
            "otherUser": other_user,
            "lastMessage": last_msg_text,
            "lastMessageAt": conv.get("lastMessageAt"),
            "unread": unread,
        })

    return result


# POST /api/conversations
@router.post("")
async def create_conversation(body: dict, user: dict = Depends(get_current_user)):
    db = get_db()
    recipient_id_str = body.get("recipientId")
    if not recipient_id_str:
        raise HTTPException(status_code=400, detail="recipientId is required")

    try:
        recipient_oid = ObjectId(recipient_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid recipientId")

    recipient = await db.users.find_one({"_id": recipient_oid})
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    # Check connection
    conn = await db.connections.find_one({
        "$or": [
            {"requester": user["_id"], "recipient": recipient_oid},
            {"requester": recipient_oid, "recipient": user["_id"]},
        ],
        "status": "accepted",
    })
    if not conn:
        raise HTTPException(status_code=403, detail="You must be connected to start a conversation")

    # Check if conversation already exists
    conversation = await db.conversations.find_one({
        "participants": {"$all": [user["_id"], recipient_oid], "$size": 2}
    })

    if not conversation:
        now = datetime.now(timezone.utc)
        doc = {
            "participants": [user["_id"], recipient_oid],
            "lastMessage": None,
            "lastMessageAt": now,
            "unreadCounts": {},
            "createdAt": now,
            "updatedAt": now,
        }
        result = await db.conversations.insert_one(doc)
        doc["_id"] = result.inserted_id
        conversation = doc

    # Populate participants
    populated_participants = []
    for pid in conversation.get("participants", []):
        p = await _populate_user(db, pid)
        if p:
            populated_participants.append(p)

    conv_response = {
        "_id": str(conversation["_id"]),
        "participants": populated_participants,
        "lastMessage": str(conversation.get("lastMessage")) if conversation.get("lastMessage") else None,
        "lastMessageAt": conversation.get("lastMessageAt"),
        "unreadCounts": conversation.get("unreadCounts", {}),
        "createdAt": conversation.get("createdAt"),
        "updatedAt": conversation.get("updatedAt"),
    }
    return conv_response


# GET /api/conversations/{conv_id}/messages
@router.get("/{conv_id}/messages")
async def get_messages(
    conv_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(40, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = user["_id"]
    conv_oid = ObjectId(conv_id)
    skip = (page - 1) * limit

    messages_cursor = db.messages.find(
        {"conversationId": conv_oid}
    ).sort("createdAt", 1).skip(skip).limit(limit)
    messages = await messages_cursor.to_list(length=limit)

    # Populate sender for each message
    result = []
    for msg in messages:
        if msg.get("sender"):
            sender = await _populate_user(db, msg["sender"])
            msg["sender"] = sender or msg["sender"]
        result.append(_serialize_message(msg))

    # Mark messages as read
    await db.messages.update_many(
        {
            "conversationId": conv_oid,
            "readBy": {"$ne": user_id},
            "sender": {"$ne": user_id},
        },
        {"$addToSet": {"readBy": user_id}},
    )

    # Reset unread count
    await db.conversations.update_one(
        {"_id": conv_oid},
        {"$set": {f"unreadCounts.{str(user_id)}": 0}},
    )

    return result


# POST /api/conversations/{conv_id}/files
@router.post("/{conv_id}/files", status_code=201)
async def upload_file(
    conv_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = user["_id"]
    conv_oid = ObjectId(conv_id)

    conversation = await db.conversations.find_one({"_id": conv_oid})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check connection
    other_id = None
    for p in conversation.get("participants", []):
        if p != user_id:
            other_id = p
            break

    if other_id:
        conn = await db.connections.find_one({
            "$or": [
                {"requester": user_id, "recipient": other_id},
                {"requester": other_id, "recipient": user_id},
            ],
            "status": "accepted",
        })
        if not conn:
            raise HTTPException(status_code=403, detail="You must be connected to send files")

    # Save file
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    import time, random, math
    unique = f"{int(time.time() * 1000)}-{random.randint(0, 10**9)}"
    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{unique}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    now = datetime.now(timezone.utc)
    msg_doc = {
        "conversationId": conv_oid,
        "sender": user_id,
        "text": "",
        "file": {
            "originalName": file.filename,
            "mimeType": file.content_type,
            "size": len(contents),
            "url": f"/uploads/{filename}",
        },
        "readBy": [user_id],
        "createdAt": now,
        "updatedAt": now,
    }

    result = await db.messages.insert_one(msg_doc)
    msg_doc["_id"] = result.inserted_id

    # Update conversation
    await db.conversations.update_one(
        {"_id": conv_oid},
        {"$set": {"lastMessage": msg_doc["_id"], "lastMessageAt": now}},
    )

    # Populate sender
    sender = await _populate_user(db, user_id)
    msg_doc["sender"] = sender or msg_doc["sender"]

    return _serialize_message(msg_doc)


# GET /api/conversations/users/search
@router.get("/users/search")
async def search_users(
    q: str = Query(""),
    user: dict = Depends(get_current_user),
):
    db = get_db()
    if not q or len(q) < 2:
        return []

    # Escape regex special chars
    escaped = re.escape(q)
    regex = {"$regex": escaped, "$options": "i"}

    users = await db.users.find(
        {
            "_id": {"$ne": user["_id"]},
            "$or": [{"username": regex}, {"displayName": regex}],
        },
        {"username": 1, "displayName": 1, "avatarUrl": 1},
    ).limit(10).to_list(length=10)

    for u in users:
        u["_id"] = str(u["_id"])

    return users
