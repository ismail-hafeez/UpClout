import time
import extract
import meta_data
import post_data
from load import Postgres
from apify_class import Apify

def get_influencer_list() -> list[str]:

    with open("../insta_profiles.txt", "r") as file:
        influencers = [line.strip() for line in file.readlines()]

    return influencers

def already_processed(username: str) -> bool:
    with open("../processed_influencers.txt", "r") as f:
        return username in {line.strip() for line in f}

def ETL():
    
    apify = Apify()
    postgres = Postgres()
    influencers = get_influencer_list()
    
    for idx, influencer in enumerate(influencers):

        if already_processed(influencer):
            continue

        path = extract.scrape_influencer(influencer, apify) # Extract
        influencerID = meta_data.clean_meta_data(path) # Transform I
        postgres.load_influencer_table(path) # Load
        post_data.clean_post_data(path, influencerID) # Transform II

        # Switch APIs every 5 scrapes
        if idx % 5 == 0:
            print("Rotating APIs")
            apify.rotate_apis()
            time.sleep(5)
            print("Sleeping for 5 seconds ... ")  

        if idx == 50:
            break
    
    postgres.close_connection()

if __name__=="__main__":
    
    start = time.time()      
    ETL()
    end = time.time()        
    print(f"Execution time: {end - start:.4f} seconds")
    