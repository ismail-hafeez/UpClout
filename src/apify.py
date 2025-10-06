from apify_client import ApifyClient
from dotenv import load_dotenv
import os, json
import requests
import pandas as pd

# Load environment variables
load_dotenv()

# Fetching values
API_TOKEN = os.getenv("API_TOKEN")

DATA_OUTPUT="../data"

# Initialize the ApifyClient with Apify API token
client = ApifyClient(API_TOKEN)

def make_folder(folderName: str) -> str:
    FOLDER_NAME=f"{DATA_OUTPUT}/{folderName}"
    os.makedirs(FOLDER_NAME, exist_ok=True)

    return f"{DATA_OUTPUT}/{folderName}/{folderName}"

def download_profil_pic(path: str, url: str) -> str:
    # Send request
    response = requests.get(url)
    # Check if download was successful
    if response.status_code == 200:
        with open(f"{path}.jpg", "wb") as f:
            f.write(response.content)
        return "Image downloaded successfully!"
    else:
        return f"Failed to download image. Status code:{response.status_code}"
 
def run_actor(input: dict) -> list:
    run = client.actor("apify/instagram-scraper").call(run_input=input)
    # Fetch scraped data into a list
    data = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        data.append(item)
    return data

def save_to_csv(PATH: str, data: list) -> pd.DataFrame:
    # Convert to pandas DataFrame
    df = pd.DataFrame(data)
    columns_to_keep=["id", "inputUrl" ,"fullName", "username", "postsCount", "biography", \
                    "followersCount", "followsCount", "profilePicUrlHD", "verified", "isBusinessAccount", "businessCategoryName"]
    df = df[columns_to_keep]
    # Saving to CSV
    df.to_csv(f"{PATH}_meta_data.csv", index=False)

    return df

def save_to_json(PATH: str, data: list) -> None:
    with open(f"{PATH}.json", "w") as file:
            json.dump(data, file, indent=4)

def scrape_post_data(instaprofile: str) -> str:

    PATH=make_folder(instaprofile)

    run_input = {
        "directUrls": [f"https://www.instagram.com/{instaprofile}/"], 
        "resultsType": "posts", 
        "resultsLimit": 50,
        "scrapeAdditionalData": True      
    }

    print("Running Instagram Scraper Actor...")
    try:
        data = run_actor(run_input)
        save_to_json(PATH, data)
        
        return f"Succesfully scraped {instaprofile}"

    except Exception as e:
        return f"Error scraping {instaprofile}: {e}"
    
def scrape_meta_data(instaprofile: str) -> str:

    PATH=make_folder(instaprofile)

    run_input = {
        "directUrls": [f"https://www.instagram.com/{instaprofile}/"], 
        "resultsType": "details", 
        "searchType": "hashtag",
        "resultsLimit": 1,
        "scrapeAdditionalData": True      
    }

    print("Running Instagram Scraper Actor...")
    try:
        data = run_actor(run_input)
        df = save_to_csv(PATH, data)
        
        # Downloading Profile Picture
        url = df['profilePicUrlHD'][0]
        pic_download_response = download_profil_pic(PATH, url)
        print(pic_download_response)

        return f"Succesfully scraped {instaprofile}"

    except Exception as e:
        return f"Error scraping {instaprofile}: {e}"