from apify_client import ApifyClient
from dotenv import load_dotenv
import os, json
import requests
import pandas as pd
from datetime import datetime
import log

"""
Defines scrapers to extract data
"""

# Load environment variables
load_dotenv()

class Apify:
    def __init__(self):
        self.API_LIST = ['API_TOKEN', 'API_TOKEN_2', 'API_TOKEN_3', 'API_TOKEN_4', 'API_TOKEN_5', 'API_TOKEN_6']
        self.DATA_OUTPUT = "../data"
        self.rotate_apis()

    # --- Helper Functions --- #

    def write_to_log_file(self, message: str) -> None:

        PATH="../logs"
        # Writing to log file
        with open(f"{PATH}/extract.log", "a", encoding="utf-8") as file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"[{timestamp}] - {message}\n")
        
    def make_folder(self, folderName: str) -> str:
        FOLDER_NAME=f"{self.DATA_OUTPUT}/{folderName}"
        os.makedirs(FOLDER_NAME, exist_ok=True)

        return f"{self.DATA_OUTPUT}/{folderName}/{folderName}"
    
    def download_profil_pic(self, path: str, df: pd.DataFrame) -> None:
        log_message: str
        url = df['profilePicUrlHD'][0]
        # Send request
        response = requests.get(url)
        # Check if download was successful
        if response.status_code == 200:
            with open(f"{path}.jpg", "wb") as f:
                f.write(response.content)
            log_message = "Image downloaded successfully!"
        else:
            log_message = f"Failed to download image. Status code:{response.status_code}"

        log.log_extract_meta_data(log_message)
    
    def save_to_csv(self, PATH: str, data: list) -> pd.DataFrame:
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        columns_to_keep=["id", "inputUrl" ,"fullName", "username", "postsCount", "biography", \
                        "followersCount", "followsCount", "profilePicUrlHD", "verified", "isBusinessAccount", "businessCategoryName"]
        df = df[columns_to_keep]
        # Saving to CSV
        df.to_csv(f"{PATH}_meta_data.csv", index=False)

        return df
    
    def save_to_json(self, PATH: str, data: list) -> None:
        with open(f"{PATH}_post_data.json", "w") as file:
                json.dump(data, file, indent=4)

    def rotate_apis(self) -> None:
        """
        This function rotates between 6 APIs to cater with usage limit and 
        consecutive API calls from a single API
        """
        current = self.API_LIST.pop()
        self.API_LIST.insert(0, current)

        self.API_TOKEN = os.getenv(current)
        self.client = ApifyClient(self.API_TOKEN)  

    # --- Scraper Functions --- #

    def run_actor(self, input: dict) -> list:
        run = self.client.actor("apify/instagram-scraper").call(run_input=input)
        # Fetch scraped data into a list
        data = []
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            data.append(item)
        return data

    def scrape_post_data(self, instaprofile: str) -> None:

        PATH=self.make_folder(instaprofile)
        run_input = {
            "directUrls": [f"https://www.instagram.com/{instaprofile}/"], 
            "resultsType": "posts", 
            "resultsLimit": 50,
            "scrapeAdditionalData": True      
        }

        print("Running Instagram Scraper Actor...")
        try:
            data = self.run_actor(run_input)
            self.save_to_json(PATH, data)
            
            log_message = f"Succesfully scraped {instaprofile}'s post data"

        except Exception as e:
            log_message = f"Error scraping {instaprofile}'s post data: {e}"
        finally:
            log.log_extract_post_data(log_message)
        
    def scrape_meta_data(self, instaprofile: str) -> int | None:

        PATH=self.make_folder(instaprofile)
        run_input = {
            "directUrls": [f"https://www.instagram.com/{instaprofile}/"], 
            "resultsType": "details", 
            "searchType": "hashtag",
            "resultsLimit": 1,
            "scrapeAdditionalData": True      
        }

        print("Running Instagram Scraper Actor...")
        try:
            data = self.run_actor(run_input)
            # If Private Account
            if data[0]['private'] == True:
                log_message = f"Skipping user: {instaprofile} because Private"
                log.log_skipped_influencer(log_message)
                return 0
            
            df = self.save_to_csv(PATH, data)
            # Downloading Profile Picture
            self.download_profil_pic(PATH, df)
            log_message = f"Succesfully scraped {instaprofile}'s meta data"

        except Exception as e:
            log_message = f"Error scraping {instaprofile}'s meta data: {e}"

        finally:
            log.log_extract_meta_data(log_message)
        
