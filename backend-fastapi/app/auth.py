from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from app.config import get_settings
from app.database import get_db
import psycopg2

settings = get_settings()
security = HTTPBearer()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

def verify_brand(username: str) -> bool:
    conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
    cur = conn.cursor()
    cur.execute("SELECT * FROM brands WHERE username = %s", (username,))
    return cur.fetchone() is not None


def hash_password(password: str) -> str:
    # Node.js bcryptjs truncates to 72 bytes automatically.
    # Python bcrypt 4.0 throws an error, so we truncate manually for compatibility.
    truncated = password.encode('utf-8')[:72]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    truncated = plain.encode('utf-8')[:72]
    return bcrypt.checkpw(truncated, hashed.encode('utf-8'))


def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"id": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def user_to_safe(user: dict) -> dict:
    """Convert a MongoDB user document to a safe response (no password)."""
    return {
        "id": str(user["_id"]),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "displayName": user.get("displayName") or user.get("username", ""),
        "avatarUrl": user.get("avatarUrl", ""),
        "cloutScore": user.get("cloutScore", 0),
        "reviewCount": user.get("reviewCount", 0),
        "userType": user.get("userType", "Influencer"),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency — equivalent of the Express `protect` middleware."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return user
