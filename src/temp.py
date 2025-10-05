import pandas as pd
from datetime import datetime
from apify import apify_actor
import time

DATA_PATH = "../data"

df=pd.read_csv(f"{DATA_PATH}/pakistan_influencers_sample.csv")

def scrape():
    size=len(df)
    
    for idx in range(5):

        current = df.iloc[idx]
        _, insta, _ = current

        if insta == "nan":
            continue

        message=apify_actor(insta)

        with open("log.log", "a") as file:
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            file.write(f"[{timestamp}] {message}\n")

        time.sleep(1)

if __name__=="__main__":

    scrape()

    