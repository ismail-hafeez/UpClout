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

