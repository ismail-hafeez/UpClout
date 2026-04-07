import psycopg2
import os
import pandas as pd
import log

BUCKET = os.getenv('AWS_S3_BUCKET')
REGION = os.getenv('AWS_REGION')

class Postgres:
    def __init__(self):
        self.conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
        self.cur = self.conn.cursor()

    # -- Helper Functions -- #
            
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

    def execute(self, query: str, params: tuple = None):
        """Execute a SELECT query and return results as list of dictionaries."""
        self.cur.execute(query, params)
        results = self.cur.fetchall()
        
        if not results:
            return []
        
        # Get column names from cursor description
        columns = [desc[0] for desc in self.cur.description]
        
        # Convert to list of dictionaries
        return [dict(zip(columns, row)) for row in results]

    # -- Storage Functions -- #

    def load_influencer_table(self, PATH: str) -> None:
        _dict = self.extract_dict_meta_data(PATH)
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

            response = f"{_dict['username']}'s Data Inserted Successfully"

        except Exception as e:
            response = f"{_dict['username']}'s Data Insertion enountered error: {e}"

        finally:
            log.log_influencer_table(response)

    def load_brand_table(self, PATH: str) -> None:
        _dict = self.extract_dict_meta_data(PATH)
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

            response = f"{_dict['username']}'s Data Inserted Successfully"

        except Exception as e:
            response = f"{_dict['username']}'s Data Insertion enountered error: {e}"

        finally:
            log.log_brand_table(response)

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

            response = f"{hashtag} Successfully Inserted"
        except Exception as e:
            response = f"{hashtag} Insertion enountered error: {e}"

        finally:
            log.log_hashtags_table(response)

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

            response = f"{postID_hashID} Successfully Inserted"
        except Exception as e:
            response = f"{postID_hashID} Insertion enountered error: {e}"

        finally:
            log.log_posts_hashtags_table(response)

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

            response = f"{_dict.get('id')} Inserted Successfully"

        except Exception as e:
            response = f"{_dict.get('id')} Insertion encountered error: {e}"

        finally:
            log.log_posts_table(response)

    def load_brand_posts_table(self, _dict: dict) -> None:
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
                    ownerid,
                    ownerbrandid
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                None,
                _dict.get("ownerID_TEMP")
            )

            self.cur.execute(query, values)
            self.conn.commit()

            response = f"{_dict.get('id')} Inserted Successfully"

        except Exception as e:
            response = f"{_dict.get('id')} Insertion encountered error: {e}"

        finally:
            log.log_posts_table(response)

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

            response = f"{username} Inserted Successfully"

        except Exception as e:
            response = f"{username} Insertion encountered error: {e}"

        finally:
            log.log_taggedUsers_table(response)

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

            response = f"{values} Successfully Inserted Successfully"

        except Exception as e:
            response = f"{values} Insertion encountered error: {e}"

        finally:
            log.log_posts_taggedUsers_table(response)

