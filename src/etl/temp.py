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

def ETL(username: str = None) -> bool:
    
    apify = Apify()
    postgres = Postgres()  

    # Extract
    try:
        path = extract.scrape_influencer(username, apify) # Extract
    except Exception as e:
        log.log_skipped_influencer(f"{username}Extract failed — {e}")
        return False

    # Skipping if private 
    if isPrivate(path, username):
        return False        

    influencerID = meta_data.clean_meta_data(path) # Transform I
    postgres.load_influencer_table(path) # Load
    post_data.clean_post_data(path, influencerID) # Transform II + Load
    
    # dump in txt file
    keep_track_influencers(username)  
 
    postgres.close_connection()
    return True

if __name__=="__main__":

    username = input("Enter username: ")   
    result = ETL(username)   
    if not result:
        print("Cannot find username on Instagram")
    else:
        print("User data extracted successfully")   