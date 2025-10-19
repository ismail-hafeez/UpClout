from apify_class import Apify
import time

def scrape_influencer(username: str, apify: Apify) -> str:
    
    apify.scrape_meta_data(username)
    time.sleep(2)
    apify.scrape_post_data(username)

    return f"../data/{username}"

def scrape_brand(username: str, apify: Apify) -> None:

    apify.scrape_meta_data(username)
    time.sleep(1)
    apify.scrape_post_data(username)

if __name__=="__main__":
    ...
