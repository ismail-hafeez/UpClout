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

DATA_PATH = "../data"

def get_influencer_list() -> list:

    with open("../insta_profiles.txt", "r") as file:
        influencers = [line.strip() for line in file.readlines()]

    return influencers

def ETL():
    
    postgres = Postgres()
    influencers = get_influencer_list()
    
    for influencer in influencers:
        path = extract.scrape_influencer("iiqraaziz") # Extract
        clean.clean_meta_data(path) # Transform
        postgres.load_influencer_table(path) # Load
        break
    
    postgres.close_connection()

if __name__=="__main__":

    ETL()
    #clean.clean_meta_data(path)
    