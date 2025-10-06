from apify_client import ApifyClient
from dotenv import load_dotenv
import os, json
import requests
import pandas as pd

"""
Defines scrapers to extract data
"""

# Load environment variables
load_dotenv()

class Apify:
    def __init__(self):
        self.API_TOKEN= os.getenv("API_TOKEN")
        self.DATA_OUTPUT="../data"
        self.client=ApifyClient(self.API_TOKEN) 

    # --- Helper Functions --- #

    def make_folder(self, folderName: str) -> str:
        FOLDER_NAME=f"{self.DATA_OUTPUT}/{folderName}"
        os.makedirs(FOLDER_NAME, exist_ok=True)

        return f"{self.DATA_OUTPUT}/{folderName}/{folderName}"
    
    def download_profil_pic(self, path: str, url: str) -> str:
        # Send request
        response = requests.get(url)
        # Check if download was successful
        if response.status_code == 200:
            with open(f"{path}.jpg", "wb") as f:
                f.write(response.content)
            return "Image downloaded successfully!"
        else:
            return f"Failed to download image. Status code:{response.status_code}"
    
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

    # --- Scraper Functions --- #

    def run_actor(self, input: dict) -> list:
        run = self.client.actor("apify/instagram-scraper").call(run_input=input)
        # Fetch scraped data into a list
        data = []
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            data.append(item)
        return data

    def scrape_post_data(self, instaprofile: str) -> str:

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
            
            return f"Succesfully scraped {instaprofile}"

        except Exception as e:
            return f"Error scraping {instaprofile}: {e}"
        
    def scrape_meta_data(self, instaprofile: str) -> str:

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
            df = self.save_to_csv(PATH, data)
            
            # Downloading Profile Picture
            url = df['profilePicUrlHD'][0]
            pic_download_response = self.download_profil_pic(PATH, url)
            print(pic_download_response)

            return f"Succesfully scraped {instaprofile}"

        except Exception as e:
            return f"Error scraping {instaprofile}: {e}"
        
