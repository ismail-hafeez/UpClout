from apify_class import Apify
import time

import importlib
import apify_class

importlib.reload(apify_class)

def scrape_influencer(username: str) -> str:
    apify = Apify()

    apify.scrape_meta_data(username)
    time.sleep(2)
    #apify.scrape_post_data(username)

    return f"../data/{username}"

def scrape_brand(username: str) -> None:
    apify = Apify()

    apify.scrape_meta_data(username)
    time.sleep(1)
    apify.scrape_post_data(username)

if __name__=="__main__":
    ...
