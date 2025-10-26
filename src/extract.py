from apify_class import Apify
import time

def scrape_influencer(username: str, apify: Apify) -> int | str:
    
    res = apify.scrape_meta_data(username)
    if res == 0:
        return 0
    time.sleep(2)
    apify.scrape_post_data(username)

    return f"../data/{username}"

def scrape_brand(username: str, apify: Apify) -> int | str:

    res = apify.scrape_meta_data(username)
    if res == 0:
        return 0
    time.sleep(2)
    apify.scrape_post_data(username)

    return f"../data/{username}"

if __name__=="__main__":
    ...
