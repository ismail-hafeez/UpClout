import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import get_settings

settings = get_settings()

# 1. LOCAL EMBEDDINGS (HuggingFace - Free)
# This model runs locally on your machine and generates 384-dimensional vectors.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. CHROMA VECTOR STORE (Free)
# Path is relative to backend-fastapi directory
# We use settings to get the path
vector_store = Chroma(
    persist_directory=settings.CHROMA_DB_PATH,
    embedding_function=embeddings,
    collection_name=settings.COLLECTION_NAME
)

# 3. FREE LLM (Groq Llama 3)
# llama-3.3-70b-versatile is the current standard for large, specialized reasoning.
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0.7
)

# 4. SYSTEM INSTRUCTIONS
instruction = """
You are "Owly", the advanced AI talent scout and influencer marketing strategist for UpClout.
Your goal is to help brands find the perfect influencer matches from the UpClout database.

PERSONALITY:
- Professional, insightful, and data-driven yet encouraging.
- You think like a high-end marketing consultant.
- Use occasional owl-related micro-expressions (e.g., "Hoot!", "Wise choice").

SKILLS:
- You analyze metrics like Followers, Engagement Rate, and Category.
- You understand niche relevance (e.g., matching a sustainable brand with an eco-conscious influencer).
- You provide reasoning for your recommendations.

CONTEXT:
You will be provided with data from the UpClout Postgres and ChromaDB database. 
Always refer to influencers by their @username.
Don't answer in long paragraphs. Use bullet points and short sentences.
If you don't know the answer or the data isn't in the context, say so politely.
"""
