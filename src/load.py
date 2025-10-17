import psycopg2
from datetime import datetime
import os
import pandas as pd

class Postgres:
    def __init__(self):
        self.conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        self.cur = self.conn.cursor()

    # -- Helper Functions -- #

    def write_to_log_file(self, message: str) -> None:

        PATH="../logs"
        #PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
        # Writing to log file
        with open(f"{PATH}/load.log", "a", encoding="utf-8") as file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"[{timestamp}] - {message}\n")
            
    def extract_dict_meta_data(self, PATH: str) -> list:
        csv_file = None
        for file in os.listdir(PATH):
            if file.endswith(".csv"):
                csv_file = os.path.join(PATH, file)
                break

        df = pd.read_csv(csv_file)
        _dict = df.iloc[0].to_dict()

        return _dict

    def close_connection(self) -> None:

        self.conn.commit()
        self.cur.close()
        self.conn.close()

    # -- Storage Function -- #

    def load_influencer_table(self, PATH: str) -> None:
        
        _dict = self.extract_dict_meta_data(PATH)
        response: str
        try:
            query = """
                INSERT INTO Influencers (
                    influencerID,
                    url,
                    name,
                    username,
                    postcount,
                    bio,
                    followers,
                    following,
                    profile_pic,
                    isVerified,
                    isbusinessaccount,
                    businesscategoryname,
                    location
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            self.cur.execute(query, tuple(_dict.values()))
            self.conn.commit()

            response = f"{_dict['username']}'s Data Inserted Successfully in Influencer Table"

        except Exception as e:
            response = f"{_dict['username']}'s Data Insertion in Influencer Table enountered error: {e}"

        finally:
            self.write_to_log_file(response)

    def load_brand_table(self, PATH: str) -> None:

        _dict = self.extract_dict_meta_data(PATH)
        response: str
        try:
            query = """
                INSERT INTO Brands (
                    brandID,
                    url,
                    name,
                    username,
                    postcount,
                    bio,
                    followers,
                    following,
                    profile_pic,
                    isVerified,
                    isbusinessaccount,
                    businesscategoryname,
                    location
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            self.cur.execute(query, tuple(_dict.values()))
            self.conn.commit()

            response = f"{_dict['username']}'s Data Inserted Successfully in Brands Table"

        except Exception as e:
            response = f"{_dict['username']}'s Data Insertion in Brands Table enountered error: {e}"

        finally:
            self.write_to_log_file(response)

    def load_hashtags_table(self, hashtag: str) -> None:
        response: str
        try:
            query = """
                INSERT INTO Hashtags (tag_name)
                VALUES (%s)
                ON CONFLICT (tag_name) DO NOTHING;
            """

            self.cur.execute(query, (hashtag,))
            self.conn.commit()

            response = f"{hashtag} Successfully Inserted in Hashtags Table"
        except Exception as e:
            response = f"{hashtag} Insertion in Hashtags Table enountered error: {e}"

        finally:
            self.write_to_log_file(response)

    def load_posts_hashtags_table(self, postID_hashID: tuple) -> None:
        response: str
        try:
            query = """
                INSERT INTO posts_hashtags (post_id, hashtag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """
            self.cur.executemany(query, postID_hashID)
            self.conn.commit()

            response = "Successfully Inserted in Hashtags and Posts Table"
        except Exception as e:
            response = f"Hashtags and Posts Table Insertion enountered error: {e}"

        finally:
            self.write_to_log_file(response)

    def load_posts_table(self, _dict: dict) -> None:
        try:
            query = """
                INSERT INTO Posts (
                    postID,
                    type,
                    caption,
                    url,
                    commentsCount,
                    likesCount,
                    timestamp,
                    isSponsored,
                    ownerid
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (postID) DO NOTHING;
            """

            values = (
                _dict.get("id"),
                _dict.get("type"),
                _dict.get("caption"),
                _dict.get("url"),
                _dict.get("commentsCount"),
                _dict.get("likesCount"),
                _dict.get("timestamp"),
                _dict.get("isSponsored"),
                _dict.get("ownerID_TEMP")
            )

            self.cur.execute(query, values)
            self.conn.commit()

            response = f"{_dict.get('id')} Post Inserted Successfully in Post Table"

        except Exception as e:
            response = f"{_dict.get('id')} Post Insertion in Post Table encountered error: {e}"

        finally:
            self.write_to_log_file(response)

    def load_taggedUsers(self, id: int, username: str) -> None:
        try:
            query = """
                INSERT INTO taggeduser (
                    taggeduserID,
                    username
                )
                VALUES (%s, %s)
                ON CONFLICT (taggeduserID) DO NOTHING;
            """

            values = (id, username)

            self.cur.execute(query, values)
            self.conn.commit()

            response = f"{username} Inserted Successfully in TaggedUser Table"

        except Exception as e:
            response = f"{username} Insertion in TaggedUser Table encountered error: {e}"

        finally:
            self.write_to_log_file(response)

    def load_posts_taggedUsers(self, postid: int, taggedUserid: int) -> None:
        try:
            query = """
                INSERT INTO posts_taggeduser (
                    postID,
                    taggeduserID
                )
                VALUES (%s, %s)
            """

            values = (postid, taggedUserid)

            self.cur.execute(query, values)
            self.conn.commit()

            response = "Successfully Inserted Successfully in Posts_TaggedUser Table"

        except Exception as e:
            response = f"Insertion in Posts_TaggedUser Table encountered error: {e}"

        finally:
            self.write_to_log_file(response)

