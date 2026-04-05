import socketio
from datetime import datetime, timezone
from bson import ObjectId
from jose import JWTError, jwt
from app.config import get_settings
from app.database import get_db

settings = get_settings()

# Create an async Socket.IO server
# Setting cors_allowed_origins as an empty list often helps with some ASGI servers to allow all
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    logger=True,
    engineio_logger=True,
)

# Map of userId -> sid for online presence
online_users: dict[str, str] = {}


async def _get_user_from_token(token: str) -> dict | None:
    """Verify JWT and return user document (no password)."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("id")
        if not user_id:
            return None
        db = get_db()
        user = await db.users.find_one(
            {"_id": ObjectId(user_id)},
            {"password": 0},
        )
        return user
    except (JWTError, Exception):
        return None


@sio.event
async def connect(sid, environ, auth=None):
    """Authenticate socket connection via JWT and populate session."""
    print(f"=== SOCKET CONNECT ATTEMPT from {sid} ===")
    print(f"Auth payload received: {auth}")

    token = None
    if isinstance(auth, dict):
        token = auth.get("token")
    elif isinstance(auth, str):
        token = auth

    if not token:
        print("SOCKET ERROR: Authentication payload missing 'token'")
        return False # Reject connection

    user = await _get_user_from_token(token)
    if not user:
        print("SOCKET ERROR: Invalid or expired JWT token")
        return False

    user_id = str(user["_id"])
    print(f"SUCCESS! Authenticated user_id: {user_id}")
    # Save user info on the session so message_send can use it
    await sio.save_session(sid, {"user": user, "userId": user_id})

    online_users[user_id] = sid
    # Tell everyone this user is online
    await sio.emit("user:online", {"userId": user_id}, skip_sid=sid)
    return True


    online_users[user_id] = sid
    # Tell everyone this user is online
    await sio.emit("user:online", {"userId": user_id}, skip_sid=sid)


@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("userId") if session else None
    if user_id:
        online_users.pop(user_id, None)
        await sio.emit("user:offline", {"userId": user_id})


@sio.on("conversation:join")
async def conversation_join(sid, conversation_id):
    sio.enter_room(sid, conversation_id)


@sio.on("conversation:leave")
async def conversation_leave(sid, conversation_id):
    sio.leave_room(sid, conversation_id)


@sio.on("message:send")
async def message_send(sid, data):
    session = await sio.get_session(sid)
    if not session:
        print("SOCKET MESSAGE ERROR: Not authenticated")
        return {"error": "Not authenticated"}

    user_id_str = session.get("userId")
    user_id = ObjectId(user_id_str)
    db = get_db()

    conversation_id = data.get("conversationId")
    text = (data.get("text") or "").strip()

    print(f"=== MESSAGE SEND ATTEMPT ===")
    print(f"from user {user_id_str} to conversation {conversation_id}")
    print(f"text: {text}")

    if not text:
        print("SOCKET MESSAGE ERROR: Message cannot be empty")
        return {"error": "Message cannot be empty"}

    conv_oid = ObjectId(conversation_id)

    # Verify sender is a participant
    conversation = await db.conversations.find_one({
        "_id": conv_oid,
        "participants": user_id,
    })
    if not conversation:
        print("SOCKET MESSAGE ERROR: Conversation not found or you are not a participant")
        return {"error": "Conversation not found"}

    # Check connection
    other_participant_id = None
    for p in conversation.get("participants", []):
        if str(p) != user_id_str:
            other_participant_id = p
            break

    if other_participant_id:
        conn = await db.connections.find_one({
            "$or": [
                {"requester": user_id, "recipient": other_participant_id},
                {"requester": other_participant_id, "recipient": user_id},
            ],
            "status": "accepted",
        })
        if not conn:
            print("SOCKET MESSAGE ERROR: Users are not connected")
            return {"error": "not_connected"}

    # Save message to DB
    now = datetime.now(timezone.utc)
    msg_doc = {
        "conversationId": conv_oid,
        "sender": user_id,
        "text": text,
        "readBy": [user_id],
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.messages.insert_one(msg_doc)
    msg_doc["_id"] = result.inserted_id

    # Populate sender
    sender_doc = await db.users.find_one(
        {"_id": user_id},
        {"username": 1, "displayName": 1, "avatarUrl": 1},
    )

    message_response = {
        "_id": str(msg_doc["_id"]),
        "conversationId": conversation_id,
        "sender": {
            "_id": user_id_str,
            "username": sender_doc.get("username", "") if sender_doc else "",
            "displayName": sender_doc.get("displayName", "") if sender_doc else "",
            "avatarUrl": sender_doc.get("avatarUrl", "") if sender_doc else "",
        },
        "text": text,
        "readBy": [user_id_str],
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

    # Update conversation metadata
    other_participants = [
        str(p) for p in conversation.get("participants", [])
        if str(p) != user_id_str
    ]

    unread_update = {}
    for pid_str in other_participants:
        current = conversation.get("unreadCounts", {}).get(pid_str, 0)
        unread_update[f"unreadCounts.{pid_str}"] = current + 1

    await db.conversations.update_one(
        {"_id": conv_oid},
        {"$set": {
            "lastMessage": msg_doc["_id"],
            "lastMessageAt": now,
            **unread_update,
        }},
    )

    print("SOCKET MESSAGE SUCCESS: Broadcasting message to room")
    # 1. Broadcast to all in the conversation room
    await sio.emit("message:new", message_response, room=str(conversation_id))
    
    # 2. ALSO emit directly to the sender (sid) to ensure they see it 
    # even if they lost room membership during a server restart
    await sio.emit("message:new", message_response, to=sid)

    # Notify recipients who may not be in the room
    for pid_str in other_participants:
        recipient_sid = online_users.get(pid_str)
        if recipient_sid:
            print(f"SOCKET MESSAGE NOTIFY: Emitting to online recipient {pid_str}")
            await sio.emit("conversation:updated", {
                "conversationId": str(conversation_id),
                "lastMessage": text,
                "lastMessageAt": now.isoformat(),
            }, to=recipient_sid)

    return {"success": True, "message": message_response}


@sio.on("typing:start")
async def typing_start(sid, data):
    session = await sio.get_session(sid)
    if not session:
        return
    user_id = session["userId"]
    username = session["user"].get("username", "")
    conversation_id = data.get("conversationId")
    if conversation_id:
        await sio.emit(
            "typing:start",
            {"userId": user_id, "username": username},
            room=conversation_id,
            skip_sid=sid,
        )


@sio.on("typing:stop")
async def typing_stop(sid, data):
    session = await sio.get_session(sid)
    if not session:
        return
    user_id = session["userId"]
    conversation_id = data.get("conversationId")
    if conversation_id:
        await sio.emit(
            "typing:stop",
            {"userId": user_id},
            room=conversation_id,
            skip_sid=sid,
        )
