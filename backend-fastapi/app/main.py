import os
import socketio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import connect_db, close_db
from app.socket_handler import sio

from app.routes.auth import router as auth_router
from app.routes.conversations import router as conversations_router
from app.routes.users import router as users_router
from app.routes.campaigns import router as campaigns_router
from app.routes.collaborations import router as collaborations_router
from app.routes.owly import router as owly_router
from app.routes.owly_conversations import router as owly_conv_router
from app.routes.analytics import router as analytics_router
from app.routes.profiles import router as profiles_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(title="UpClout API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include API routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(users_router)
app.include_router(campaigns_router)
app.include_router(collaborations_router)
app.include_router(owly_router)
app.include_router(owly_conv_router)
app.include_router(analytics_router)
app.include_router(profiles_router)

# Create the SIO ASGI application
sio_asgi_app = socketio.ASGIApp(sio)

# Mount the SIO app at the path /socket.io
app.mount("/socket.io", sio_asgi_app)

# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok"}
