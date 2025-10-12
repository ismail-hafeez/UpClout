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

def ETL():
    
    apify = Apify()
    postgres = Postgres()
    influencers = get_influencer_list()
    
    for idx, influencer in enumerate(influencers):
        path = extract.scrape_influencer("sajalaly") # Extract
        clean.clean_meta_data(path) # Transform
        postgres.load_influencer_table(path) # Load
        break
        # Switch APIs every 5 scrapes
        if idx % 5 == 0:
            apify.rotate_apis()
            time.sleep(5)
        
    
    postgres.close_connection()

if __name__=="__main__":

    #ETL()
    start = time.time()      

    clean.clean_post_data("../data/mahirahkhan")

    end = time.time()        
    print(f"Execution time: {end - start:.4f} seconds")
    