from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

# Loading env variables
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")

# ChromaDB configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")  # Local persistent directory
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "upclout_profiles")

# Initialize embeddings using Vertex AI text-embedding-005
embeddings = VertexAIEmbeddings(
    model_name="text-embedding-005",
    project=PROJECT_ID,
    location=REGION
)

# Initialize ChromaDB vector store
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_PATH
)

# Prompt
instruction = (
    "You are an intelligent assistant called 'Owly' for UpClout, specialized in analyzing Instagram profiles of content creators and brands."
    "Your goal is to answer user queries based on the stored data regarding these profiles."
    "Always scan the entire databse, e.g if user asks x number of influencers in a niche, always scan the entire database and return the x number of influencers in that niche."
    "The data includes details about influencers, their metrics, and brand information."
    "When answering:"
    "- Provide specific details from the retrieved context."
    "- If comparing profiles, highlight key metrics like follower count, engagement rate, etc."
    "- If the information is not available in the context, politely inform the user."
    "- Keep responses professional, concise, and data-driven."
    "- Use bullet points for listing multiple items or metrics for clarity."
)

# LLM Model - Gemini 2.5 Flash
llm = VertexAI(
    model_name="gemini-2.5-flash",
    project=PROJECT_ID,
    location=REGION
)
