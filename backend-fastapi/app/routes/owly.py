import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId

from app.auth import get_current_user
from app.database import get_db
from app.chatbot import call_model
from app.db_utils import get_connection

router = APIRouter(prefix="/api/owly", tags=["owly"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


def _fetch_user_context(username: str, user_type: str) -> dict:
    """Fetch user profile details from PostgreSQL for Owly's system prompt."""
    table = "brands" if user_type == "Brand" else "influencers"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            f"SELECT username, followers, following, businesscategoryname, location "
            f"FROM {table} WHERE username = %s LIMIT 1",
            (username,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                "username": row[0],
                "user_type": user_type,
                "followers": row[1] or 0,
                "following": row[2] or 0,
                "niche": row[3] or "General",
                "location": row[4] or "Unknown",
            }
    except Exception as e:
        print(f"Error fetching user context from PG: {e}")

    # Fallback if PG lookup fails
    return {
        "username": username,
        "user_type": user_type,
        "followers": "Unknown",
        "following": "Unknown",
        "niche": "Unknown",
        "location": "Unknown",
    }


def _generate_title(message: str) -> str:
    """Generate a short conversation title from the first message."""
    title = message.strip()[:60]
    if len(message.strip()) > 60:
        title += "..."
    return title


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Authenticated streaming chat endpoint for Owly.
    
    - If conversation_id is provided, loads history from MongoDB and appends.
    - If conversation_id is null, creates a new conversation.
    - Injects user profile context from PostgreSQL into the system prompt.
    - Persists both user message and Owly response to MongoDB.
    """
    db = get_db()
    user_id = user["_id"]
    username = user.get("username", "")
    user_type = user.get("userType", "Influencer")

    # 1. Fetch user context from PostgreSQL
    user_context = _fetch_user_context(username, user_type)

    # 2. Load or create conversation
    conversation_history = []
    conv_id = None

    if req.conversation_id:
        try:
            conv_doc = await db.owly_conversations.find_one({
                "_id": ObjectId(req.conversation_id),
                "user_id": user_id
            })
            if conv_doc:
                conv_id = conv_doc["_id"]
                conversation_history = conv_doc.get("messages", [])
        except Exception:
            pass  # Invalid ObjectId or not found — will create new

    if conv_id is None:
        # Create new conversation
        now = datetime.now(timezone.utc)
        new_conv = {
            "user_id": user_id,
            "title": _generate_title(req.message),
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        result = await db.owly_conversations.insert_one(new_conv)
        conv_id = result.inserted_id

    # 3. Call the model (CPU-bound, run in executor)
    async def generate():
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            None,
            call_model,
            req.message,
            conversation_history,
            user_context
        )

        # 4. Persist both messages to MongoDB
        now = datetime.now(timezone.utc)
        user_msg = {"role": "user", "content": req.message, "timestamp": now}
        assistant_msg = {"role": "assistant", "content": answer, "timestamp": now}

        await db.owly_conversations.update_one(
            {"_id": conv_id},
            {
                "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
                "$set": {"updated_at": now}
            }
        )

        yield answer

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "X-Conversation-ID": str(conv_id),
            "Access-Control-Expose-Headers": "X-Conversation-ID"
        }
    )
