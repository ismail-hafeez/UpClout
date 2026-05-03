import psycopg2
from dotenv import load_dotenv
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src import log 
from db_utils import get_connection

# Load environment variables
load_dotenv()

class CreateDataBase:
    def __init__(self):
        #self.POSTGRES_API=os.getenv("POSTGRES_CONNECTION")
        #self.conn = psycopg2.connect(POSTGRES_API)
        #self.cur = conn.cursor()
        self.conn = get_connection()
        self.cur = self.conn.cursor()

    def influencer_table(self) -> None:
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

            self.cur.execute(query)
            self.conn.commit()

            response = "Influencer Table created successfully"

        except Exception as e:
            response = f"Influencer Table enountered error: {e}"

        finally:
            log.log_db_donfig(response) 

    def brand_table(self) -> None:
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

            self.cur.execute(query)
            self.conn.commit()

            response = "Brand Table created successfully"

        except Exception as e:
            response = f"Brand Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def review_table(self) -> None:
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

            self.cur.execute(query)
            self.conn.commit()

            response = "Review Table created successfully"

        except Exception as e:
            response = f"Review Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def hashtags_table(self) -> None:
        try:
            query = """
                CREATE TABLE IF NOT EXISTS Hashtags (
                    hashtagID INT SERIAL PRIMARY KEY,
                    tag_name VARCHAR(255) UNIQUE
                );
            """

            self.cur.execute(query)
            self.conn.commit()

            response = "Hashtags Table created successfully"

        except Exception as e:
            response = f"Hashtags Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def posts_table(self) -> None:
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
                FOREIGN KEY (ownerID) REFERENCES influencers(influencerID),
                FOREIGN KEY (ownerBRANDID) REFERENCES brands(brandID)
            );
            """

            self.cur.execute(query)
            self.conn.commit()

            response = "Posts Table created successfully"

        except Exception as e:
            response = f"Posts Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def posts_hashtags_table(self) -> None:
        try:
            query = """
                CREATE TABLE posts_hashtags (
                post_id BIGINT REFERENCES posts(postID),
                hashtag_id INT REFERENCES hashtags(hashtagid),
                PRIMARY KEY (post_id, hashtag_id)
            );
            """

            self.cur.execute(query)
            self.conn.commit()

            response = "Posts-Hashtags Table created successfully"

        except Exception as e:
            response = f"Posts-Hashtags Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def taggedUser_table(self) -> None:
        response: str
        try:
            query = """
                CREATE TABLE IF NOT EXISTS TaggedUser (
                TaggedUserID INT PRIMARY KEY,
                username VARCHAR(255)
            );
            """
            self.cur.execute(query)
            self.conn.commit()

            response = "TaggedUser Table created successfully"

        except Exception as e:
            response = f"TaggedUser Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def posts_taggedUser_table(self) -> None:
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
            self.cur.execute(query)
            self.conn.commit()

            response = "Posts_TaggedUser Table created successfully"

        except Exception as e:
            response = f"Posts_TaggedUser Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def mentions_table(self) -> None:
        try:
            query = """
                CREATE TABLE IF NOT EXISTS Mentions (
                MentionID INT PRIMARY KEY,
                username VARCHAR(255)
            );
            """
            self.cur.execute(query)
            self.conn.commit()

            response = "Mentions Table created successfully"

        except Exception as e:
            response = f"Mentions Table enountered error: {e}"

        finally:
            log.log_db_donfig(response)

    def rising_stars_table(self) -> None:
        try:
            query = """
                CREATE TABLE IF NOT EXISTS rising_stars (
                    id BIGINT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE,
                    followers BIGINT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id) REFERENCES influencers(influencerID)
                );
            """
            self.cur.execute(query)
            self.conn.commit()
            response = "Rising Stars Table created successfully"
        except Exception as e:
            response = f"Rising Stars Table encountered error: {e}"
        finally:
            log.log_db_donfig(response)

    def create_db(self) -> str:
        try:
            # -- All the tables -- #
            self.influencer_table()
            self.brand_table()
            self.review_table()
            self.posts_table()
            self.hashtags_table()
            self.posts_hashtags_table()
            self.taggedUser_table()
            self.posts_taggedUser_table()
            self.rising_stars_table()
            # ... add more tables here

            self.conn.commit()
            self.cur.close()
            self.conn.close()
            return "All tables created successfully!" # need to change this!

        except Exception as e:
            return f"Error connecting to Database: {e}"

if __name__=="__main__":

    # Creating database
    create_db_obj = CreateDataBase() 
    response = create_db_obj.create_db()
    log.log_db_donfig(response) 