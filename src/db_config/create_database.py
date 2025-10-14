import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

#POSTGRES_API=os.getenv("POSTGRES_CONNECTION")

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
            CREATE TABLE IF NOT EXISTS Brands (
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

def review_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS Reviews (
                reviewID INT PRIMARY KEY,
                review_date TIMESTAMP,
                comment TEXT,
                reviewer_type VARCHAR(255),
                reviewerID INT,
                reviewee_type VARCHAR(255),
                revieweeID INT,
                rating INT
            );
        """

        cur.execute(query)
        conn.commit()

        response="Review Table created successfully"

    except Exception as e:
        response=f"Review Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def hashtags_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS Hashtags (
                hashtagID INT SERIAL PRIMARY KEY,
                tag_name VARCHAR(255) UNIQUE
            );
        """

        cur.execute(query)
        conn.commit()

        response="Hashtags Table created successfully"

    except Exception as e:
        response=f"Hashtags Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def posts_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS posts (
            postID BIGINT PRIMARY KEY,
            caption TEXT,
            type VARCHAR(255),
            url VARCHAR(255),
            likes INT,
            comment_count INT,
            is_collaboration BOOLEAN,
            created_at TIMESTAMP
            ownerID BIGINT,
            FOREIGN KEY (ownerID) REFERENCES influencer(influencerID)
        );
        """

        cur.execute(query)
        conn.commit()

        response="Posts Table created successfully"

    except Exception as e:
        response=f"Posts Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def posts_hashtags_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE posts_hashtags (
            post_id BIGINT REFERENCES posts(postID),
            hashtag_id INT REFERENCES hashtags(hashtagid),
            PRIMARY KEY (post_id, hashtag_id)
        );
        """

        cur.execute(query)
        conn.commit()

        response="Posts-Hashtags Table created successfully"

    except Exception as e:
        response=f"Posts-Hashtags Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def taggedUser_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS TaggedUser (
            TaggedUserID INT PRIMARY KEY,
            username VARCHAR(255)
        );
        """
        cur.execute(query)
        conn.commit()

        response="TaggedUser Table created successfully"

    except Exception as e:
        response=f"TaggedUser Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def posts_taggedUser_table(cur, conn) -> None:
    response: str
    try:
        query = """
           CREATE TABLE IF NOT EXISTS Posts_TaggedUser (
            postID BIGINT,
            TaggedUserID INT,
            PRIMARY KEY (postID, TaggedUserID),
            FOREIGN KEY (postID) REFERENCES posts(postID) ON DELETE CASCADE,
            FOREIGN KEY (TaggedUserID) REFERENCES TaggedUser(TaggedUserID) ON DELETE CASCADE
        );
        """
        cur.execute(query)
        conn.commit()

        response="Posts_TaggedUser Table created successfully"

    except Exception as e:
        response=f"Posts_TaggedUser Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def mentions_table(cur, conn) -> None:
    response: str
    try:
        query = """
            CREATE TABLE IF NOT EXISTS Mentions (
            MentionID INT PRIMARY KEY,
            username VARCHAR(255)
        );
        """
        cur.execute(query)
        conn.commit()

        response="Mentions Table created successfully"

    except Exception as e:
        response=f"Mentions Table enountered error: {e}"

    finally:
        write_to_log_file(response)

def create_db() -> str:

    try:
        #conn = psycopg2.connect(POSTGRES_API)
        #cur = conn.cursor()

        conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        cur = conn.cursor()

        # -- All the tables -- #
        influencer_table(cur, conn)
        brand_table(cur, conn)
        review_table(cur, conn)
        posts_table(cur, conn)
        hashtags_table(cur, conn)
        posts_hashtags_table(cur, conn)
        taggedUser_table(cur, conn)
        posts_taggedUser_table(cur, conn)
        # ... add more tables here

        conn.commit()
        cur.close()
        conn.close()
        return "All tables created successfully!" # need to change this!

    except Exception as e:
        return f"Error connecting to Database: {e}"

def write_to_log_file(message: str) -> None:

    PATH="../../logs"
    #PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
    # Writing to log file
    with open(f"{PATH}/db_config.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")


if __name__=="__main__":

    # Creating database 
    response=create_db()
    write_to_log_file(response)