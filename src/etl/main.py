import time
import shutil
import os, json
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

    with open("../../insta_profiles.txt", "r") as file:
        influencers = [line.strip() for line in file.readlines()]

    return influencers

def already_processed(username: str) -> bool:
    with open("../../processed_influencers.txt", "r") as f:
        return username in {line.strip() for line in f}

def keep_track_influencers(influencer: str) -> None:
    with open("../../processed_influencers.txt", "a") as f:
        f.write(f"{influencer}\n")

def get_post_data_dict(path: str) -> dict:
    json_file = None
    for file in os.listdir(path):
        if file.endswith(".json"):
            json_file = os.path.join(path, file)
            break
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data[0]

def isPrivate(response: any, username: str) -> bool:   
    path: str = f"../../data/{username}"
         
    if response == 0:
        delete_folder(path)
        return True
    else:
        user_dict = get_post_data_dict(path)

        if 'error' in user_dict.keys():
            if user_dict['error'] == "not_found" or user_dict['errorDescription'] == "Post does not exist":
                log.log_skipped_influencer(f"{username} Extract failed - PROFILE NOT FOUND")
                delete_folder(path)
                return True
        else:
            return False

def ETL():
    
    apify = Apify()
    postgres = Postgres()
    influencers = get_influencer_list()

    count: int = 1
   
    for idx, influencer in enumerate(influencers):

        if already_processed(influencer):
            continue

        influencer='alymaliha'

        # Switch APIs every 5 scrapes
        if count % 4 == 0:
            print("Rotating APIs")
            apify.rotate_apis()
            print("Sleeping for 5 seconds ... ")  
            time.sleep(5)

        if count == 10:
            print("Taking long break ... ")  
            time.sleep(60)

        print(f"{idx}: {influencer}")

        # Extract
        try:
            path = extract.scrape_influencer(influencer, apify) # Extract
        except Exception as e:
            log.log_skipped_influencer(f"{influencer}Extract failed — {e}")
            continue

        # Skipping if private 
        #if isPrivate(path, influencer):
            #continue        

        influencerID = meta_data.clean_meta_data(path) # Transform I
        postgres.load_influencer_table(path) # Load
        post_data.clean_post_data(path, influencerID) # Transform II + Load

        # dump in txt file
        keep_track_influencers(influencer)  
        count+=1

        break

    postgres.close_connection()

if __name__=="__main__":
    
    start = time.time()      
    ETL()
    end = time.time()        
    print(f"Execution time: {end - start:.4f} seconds")
