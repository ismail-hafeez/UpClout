from langchain_google_vertexai import (
    VertexAI, VertexAIEmbeddings, 
    VectorSearchVectorStore)
from dotenv import load_dotenv
import os

load_dotenv()
# loading env variables
PROJECT_ID=os.getenv("PROJECT_ID")
REGION=os.getenv("REGION")
INDEX_ID=os.getenv("INDEX_ID")
ENDPOINT_ID=os.getenv("ENDPOINT_ID")
BUCKET_NAME=os.getenv("BUCKET_NAME")

# Initializing vector store
embeddings = VertexAIEmbeddings(model_name="text-embedding-005") 
vector_store =  VectorSearchVectorStore.from_components(
    project_id=PROJECT_ID,
    region=REGION,
    gcs_bucket_name=BUCKET_NAME,
    index_id=INDEX_ID,
    endpoint_id=ENDPOINT_ID,
    embedding=embeddings,
    batch_size=1000,
    stream_update=True
)

# Prompt
instruction = (
    "You are an intelligent assistant called 'Owly' for UpClout, specialized in analyzing Instagram profiles of content creators and brands."
    "Your goal is to answer user queries based on the stored data regarding these profiles."
    "The data includes details about influencers, their metrics, and brand information."
    "When answering:"
    "- Provide specific details from the retrieved context."
    "- If comparing profiles, highlight key metrics like follower count, engagement rate, etc."
    "- If the information is not available in the context, politely inform the user."
    "- Keep responses professional, concise, and data-driven."
    "- Use bullet points for listing multiple items or metrics for clarity."
)

# LLM Model
llm = VertexAI(model_name="gemini-2.5-flash")