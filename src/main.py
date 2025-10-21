import time
import shutil
import os
import extract
import meta_data
import post_data
from load import Postgres
from apify_class import Apify
import log

def delete_folder(path: str) -> None:
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)
        print(f"Deleted folder: {path}")
    else:
        print(f"Folder not found: {path}")

def get_influencer_list() -> list[str]:

    with open("../insta_profiles.txt", "r") as file:
        influencers = [line.strip() for line in file.readlines()]

    return influencers

def already_processed(username: str) -> bool:
    with open("../processed_influencers.txt", "r") as f:
        return username in {line.strip() for line in f}

def keep_track_influencers(influencer: str) -> None:
    with open("../processed_influencers.txt", "a") as f:
        f.write(f"{influencer}\n")

def isPrivate(response: any, username: str) -> bool:
    if response == 0:
        delete_folder(f"../data/{username}")
        return True
    return False

def ETL():
    
    apify = Apify()
    postgres = Postgres()
    influencers = get_influencer_list()
   
    for idx, influencer in enumerate(influencers):

        if already_processed(influencer):
            continue

        # Extract
        try:
            path = extract.scrape_influencer(influencer, apify) # Extract
        except Exception as e:
            log.log_skipped_influencer(influencer, f"Extract failed — {e}")
            continue

        # If scraper failed or profile invalid
        if not path:
            print(f"Skipping {influencer} — invalid or deleted profile.")
            continue

        # Skipping if private 
        if isPrivate(path, influencer):
            continue        

        influencerID = meta_data.clean_meta_data(path) # Transform I
        postgres.load_influencer_table(path) # Load
        post_data.clean_post_data(path, influencerID) # Transform II

        # dump in txt file
        keep_track_influencers(influencer)  

        # Switch APIs every 5 scrapes
        if idx % 2 == 0:
            print("Rotating APIs")
            apify.rotate_apis()
            time.sleep(5)
            print("Sleeping for 5 seconds ... ")  

        if idx == 10:
            break
    
    postgres.close_connection()

if __name__=="__main__":
    
    start = time.time()      
    ETL()
    end = time.time()        
    print(f"Execution time: {end - start:.4f} seconds")
    