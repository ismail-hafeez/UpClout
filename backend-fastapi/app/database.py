from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None  # type: ignore
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_name = settings.MONGODB_URI.rsplit("/", 1)[-1].split("?")[0]
    db = client[db_name]
    print(f"MongoDB connected to '{db_name}'")


async def close_db():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


def get_db():
    return db
