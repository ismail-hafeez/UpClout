from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/owly/conversations", tags=["owly-conversations"])


@router.get("")
async def list_conversations(user: dict = Depends(get_current_user)):
    """List all Owly conversations for the authenticated user, newest first."""
    db = get_db()
    cursor = db.owly_conversations.find(
        {"user_id": user["_id"]},
        {
            "title": 1,
            "created_at": 1,
            "updated_at": 1,
            "messages": {"$slice": -1}  # Only last message for preview
        }
    ).sort("updated_at", -1)

    conversations = []
    async for doc in cursor:
        last_msg = doc.get("messages", [])
        preview = ""
        if last_msg:
            preview = last_msg[0].get("content", "")[:80]

        conversations.append({
            "_id": str(doc["_id"]),
            "title": doc.get("title", "Untitled"),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
            "last_message_preview": preview,
        })

    return conversations


@router.get("/{conv_id}/messages")
async def get_conversation_messages(conv_id: str, user: dict = Depends(get_current_user)):
    """Load full message history for a specific conversation."""
    db = get_db()
    try:
        doc = await db.owly_conversations.find_one({
            "_id": ObjectId(conv_id),
            "user_id": user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    if not doc:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Convert timestamps to ISO strings for JSON serialization
    messages = []
    for msg in doc.get("messages", []):
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg.get("timestamp", "").isoformat() if hasattr(msg.get("timestamp", ""), "isoformat") else str(msg.get("timestamp", "")),
        })

    return {
        "_id": str(doc["_id"]),
        "title": doc.get("title", "Untitled"),
        "messages": messages,
    }


@router.post("")
async def create_conversation(user: dict = Depends(get_current_user)):
    """Create a new empty Owly conversation."""
    db = get_db()
    now = datetime.now(timezone.utc)
    new_conv = {
        "user_id": user["_id"],
        "title": "New Conversation",
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db.owly_conversations.insert_one(new_conv)
    return {
        "_id": str(result.inserted_id),
        "title": "New Conversation",
        "created_at": now,
        "updated_at": now,
    }


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str, user: dict = Depends(get_current_user)):
    """Delete an Owly conversation."""
    db = get_db()
    try:
        result = await db.owly_conversations.delete_one({
            "_id": ObjectId(conv_id),
            "user_id": user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "deleted"}
