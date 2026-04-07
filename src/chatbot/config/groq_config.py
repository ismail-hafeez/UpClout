from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

# ChromaDB configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db_groq")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "upclout_profiles")

# 1. FREE EMBEDDINGS (Local)
# This uses your CPU to generate embeddings for free.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. VECTOR STORE
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_PATH
)

# 3. FREE LLM (Groq Llama 3)
# llama-3.3-70b-versatile is the current standard for large, specialized reasoning.
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

# Prompt
instruction = (
    "You are an intelligent assistant called 'Owly' for UpClout, specialized in analyzing Instagram profiles of content creators and brands."
    "Your goal is to answer user queries based on the stored data regarding these profiles."
    "Always scan the entire database, e.g if user asks x number of influencers in a niche, always scan the entire database and return the x number of influencers in that niche."
    "The data includes details about influencers, their metrics, and brand information."
    "When answering:"
    "- Provide specific details from the retrieved context."
    "- If comparing profiles, highlight key metrics like follower count, engagement rate, etc."
    "- If the information is not available in the context, politely inform the user."
    "- Keep responses professional, concise, and data-driven."
    "- Use bullet points for listing multiple items or metrics for clarity."
)
