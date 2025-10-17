import pandas as pd
from datetime import datetime
import time

import importlib
import extract
importlib.reload(extract)
import clean
importlib.reload(clean)
import load
importlib.reload(load)
from load import Postgres
import apify_class
importlib.reload(apify_class)
from apify_class import Apify

DATA_PATH = "../data"

def get_influencer_list() -> list:

    with open("../insta_profiles.txt", "r") as file:
        influencers = [line.strip() for line in file.readlines()]

    return influencers

def write_to_log_file(message: str) -> None:

    PATH="../logs"
    # Writing to log file
    with open(f"{PATH}/time_ETL.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def ETL():
    
    apify = Apify()
    postgres = Postgres()
    #influencers = get_influencer_list()
    influencers = [
        "mtpasha_",
        "isaa_akhn",
        "californiakistan",
        "megpakistan",
        "alifsay",
        "mahnooraamirr",
        "nylarajah",
        "makeupbynoormir",
        "factnamas",
        "kashaff_alii",
        "waniaaanadeem"
    ]
    
    for idx, influencer in enumerate(influencers):
        #start = time.time()
        #path = extract.scrape_influencer(influencer) # Extract
        #end = time.time()
        #mssg: str = f"{influencer} EXTRACTION time: {end - start:.4f} seconds"
        #write_to_log_file(mssg)

        path = f"../data/{influencer}"
        print(f"Current Influencer: {influencer}")

        start = time.time()
        influencerID = clean.clean_meta_data(path) # Transform I
        end = time.time()
        mssg: str = f"{influencer} META DATA CLEANING time: {end - start:.4f} seconds"
        write_to_log_file(mssg)

        start = time.time()
        clean.clean_post_data(path, influencerID) # Transform II
        end = time.time()
        mssg: str = f"{influencer} META POST CLEANING + LOADING time: {end - start:.4f} seconds"
        write_to_log_file(mssg)

        start = time.time()
        postgres.load_influencer_table(path) # Load
        end = time.time()
        mssg: str = f"{influencer} LOADING (MD) time: {end - start:.4f} seconds"
        write_to_log_file(mssg)

        # Switch APIs every 5 scrapes
        if idx % 3 == 0:
            print("Rotating APIs")
            apify.rotate_apis()
            time.sleep(5)
            print("Sleeping for 5 seconds ... ")
        if idx == 10:
            break
    
    postgres.close_connection()

if __name__=="__main__":
    #postgres = Postgres()
    
    start = time.time()      
    ETL()
    end = time.time()        
    print(f"Execution time: {end - start:.4f} seconds")
    