from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PORT: int = 5000
    MONGODB_URI: str = "mongodb://localhost:27017/upclout"
    JWT_SECRET: str = "your_super_secret_jwt_key_change_this_in_production"
    CLIENT_URL: str = "http://localhost:3000"
    
    # AI/Chatbot Settings
    GROQ_API_KEY: str = ""
    CHROMA_DB_PATH: str = "../chroma_db_groq"
    COLLECTION_NAME: str = "upclout_profiles"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
