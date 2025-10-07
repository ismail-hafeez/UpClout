import pandas as pd
from datetime import datetime
from apify_class import Apify
import time

DATA_PATH = "../data"

def scrape(apify: Apify) -> None:
    size=len(df)
    
    for idx in range(5):

        current = df.iloc[idx]
        _, insta, _ = current

        if insta == "nan":
            continue

        result=apify.scrape_meta_data(instaProfile)
        print(result)
        result_2=apify.scrape_post_data(instaProfile)
        print(result_2)

        with open("logFile.log", "a") as file:
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            file.write(f"[{timestamp}]-{result}-{result_2}\n")

        time.sleep(1)

if __name__=="__main__":

    instaProfile = "humzaamin"

    apify=Apify()

    #scrape(apify)

    result=apify.scrape_meta_data(instaProfile)
    print(result)
    result_2=apify.scrape_post_data(instaProfile)
    print(result_2)


    