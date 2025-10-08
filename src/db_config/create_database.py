import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

POSTGRES_API=os.getenv("POSTGRES_CONNECTION")

def influencer_table(cur, conn) -> None:

    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS Influencers (
                influencerID INT PRIMARY KEY,
                name VARCHAR(255),
                username VARCHAR(255) UNIQUE,
                followers BIGINT,
                following BIGINT,
                postCount BIGINT,
                bio TEXT,
                niche VARCHAR(255),
                cloutScore INT,	
                location VARCHAR(255),
                type VARCHAR(255),
                isVerified BOOLEAN
            );
        """

        cur.execute(query)
        conn.commit()

        response="Influencer Table created successfully"

    except Exception as e:
        response=f"Influencer Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def brand_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS Influencers (
                brandID INT PRIMARY KEY,
                name VARCHAR(255),
                username VARCHAR(255) UNIQUE,
                followers BIGINT,
                following BIGINT,
                postCount BIGINT,
                bio TEXT,
                niche VARCHAR(255),
                cloutScore INT,	
                type VARCHAR(255),
                isVerified BOOLEAN
            );
        """

        cur.execute(query)
        conn.commit()

        response="Brand Table created successfully"

    except Exception as e:
        response=f"Brand Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def create_db() -> str:

    conn = psycopg2.connect(POSTGRES_API)
    cur = conn.cursor()

    # -- All the tables -- #
    influencer_table(cur, conn)
    brand_table(cur, conn)
    # ... add more tables here

    conn.commit()
    cur.close()
    conn.close()

    return "All tables created successfully!"

def write_to_log_file(message: str) -> None:

    PATH="../logs"
    # Writing to log file
    with open(f"{PATH}/db_config.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

if __name__=="__main__":

    response=create_db()
    write_to_log_file(response)