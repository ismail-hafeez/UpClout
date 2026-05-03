"""
This module contains utility functions for database operations.
Returns a connection to the database.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection() -> psycopg2.connect:
    """Single source of truth for all DB connections."""
    #url = os.getenv("POSTGRES_CONNECTION")
    #if url:
    #    return psycopg2.connect(url)
    # Fallback for local dev
    #return psycopg2.connect(
        #database="postgres",#os.getenv("PG_DB", "postgres"),
        #user="postgres",#os.getenv("PG_USER", "postgres"),
        #password="1040"#os.getenv("PG_PASSWORD", "1040"),
        #host=os.getenv("PG_HOST", "localhost"),
        #port=os.getenv("PG_PORT", "5432"),
    #)
    return psycopg2.connect(database="postgres", user="postgres", password=1040)