from apify_client import ApifyClient
from dotenv import load_dotenv
import os, json

# Load environment variables
load_dotenv()

# Fetching values
API_TOKEN = os.getenv("API_TOKEN")

DATA_OUTPUT="../temp_data"

# Initialize the ApifyClient with Apify API token
client = ApifyClient(API_TOKEN)

def apify_actor(instaprofile: str) -> str:

    # Prepare the Actor input for the Instagram Scraper
    # This example scrapes posts from a specific profile
    run_input = {
        "directUrls": [f"https://www.instagram.com/{instaprofile}/"],  # URL of the Instagram profile
        "resultsType": "posts",  # Specify to scrape posts
        "resultsLimit": 50,
        "scrapeAdditionalData": True      # Limit the number of results
    }

    # Run the Instagram Scraper Actor and wait for it to finish
    # The 'apify/instagram-scraper' is a pre-built Actor available on Apify Store
    print("Running Instagram Scraper Actor...")
    try:
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        #print(f"Actor run finished. Check logs: https://console.apify.com/actors/apify/instagram-scraper/runs/{run['id']}")

        # Fetch scraped data into a list
        data = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            data.append(item)

        with open(f"{DATA_OUTPUT}/{instaprofile}.json", "w") as file:
            json.dump(data, file, indent=4)

        print(f"\nData saved successfully to {instaprofile}.json")
        #print(f"\nData also available in dataset: https://console.apify.com/storage/datasets/{run['defaultDatasetId']}")
        return f"Succesfully scraped {instaprofile}"

    except Exception as e:
        return f"Error scraping {instaprofile}: {e}"