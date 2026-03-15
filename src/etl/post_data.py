import pandas as pd 
import json 
import os, re
import shutil
from datetime import datetime, timezone

from load import Postgres
import psycopg2

from apify_class import Apify

def get_post_dict(current_folder: str) -> list[dict]:
    json_file = None
    for file in os.listdir(current_folder):
        if file.endswith(".json"):
            json_file = os.path.join(current_folder, file)
            break

    with open(json_file, "r", encoding="utf-8") as file:
        data=json.load(file)
   
    return data

def keep_useful_keys(_dict: dict) -> dict:
    keys_of_interest = [
        "id",
        "type",
        "caption",
        "hashtags", #list
        "mentions", #list
        "url",
        "commentsCount",
        "likesCount",
        "timestamp",
        "ownerUsername",
        "ownerId",
        "taggedUsers",
        "coauthorProducers",
        "ownerFullName",
        "isSponsored",
    ]
    new_dict = {k: v for k, v in _dict.items() if k in keys_of_interest}

    return new_dict

def correct_dtypes_post(_dict: dict) -> dict:
    convert_to_int = ['id', 'commentsCount', 'likesCount', 'ownerId']

    for key, value in _dict.items():
        if key == 'timestamp' and isinstance(value, str):
            try:
                _dict[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            except ValueError:
                _dict[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)

        elif key in convert_to_int:
            try:
                _dict[key] = int(value)
            except (ValueError, TypeError):
                _dict[key] = None

        elif isinstance(value, (list, dict)) or value is None:
            # keep lists, dicts, and None as they are
            _dict[key] = value

        else:
            _dict[key] = str(value)

    return _dict

def handle_taggedUsers(postID: int, taggedUsers: list) -> None:
    
    postgres = Postgres()

    for user_dict in taggedUsers:
        id = int(user_dict.get("id"))
        username = user_dict.get("username")
        # Storing in TaggedUser Table        
        postgres.load_taggedUsers(id, username)
        # Storing in Posts_taggeduser table (N:M)
        postgres.load_posts_taggedUsers(postID, id)

    postgres.close_connection()

def mention_exists(username: str) -> bool:
    conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
    cur = conn.cursor()

    query = """
        SELECT EXISTS (
            SELECT 1
            FROM influencers
            WHERE username = %s
        );
    """
    cur = conn.cursor()
    cur.execute(query, (username,))
    result = cur.fetchone()[0]
    cur.close()
    
    return result

def above_follower_threshold(username: str) -> bool:
    threshold: int = 1000
    # Scrape Meta Data
    apify = Apify()
    apify.scrape_meta_data(username)

    # If followers < 1000 -> DISCARD
    folder_path = f"../data/{username}"
    df = pd.read_csv(f"{folder_path}/{username}_meta_data.csv")
    
    followers = int(df['followersCount'][0])
    if followers >= threshold:
        return 1
    else:
        # delete folder
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            return 0

def is_influencer(usernanme: str) -> bool:
    ...

def handle_mentions(postID: int, mentions: list) -> None:
    if not mentions:
        return
    
    for username in mentions:
        if mention_exists(username):
            pass
        if not above_follower_threshold(username):
            continue
        if is_influencer(username):
            # Add to mentions table
            # Add to posts_mentions
            # Add to insta_profiles.txt
            ...
        else: 
            # Is brand
            # do something else
            ...        
        ...

def handle_coauthors(postID: int, taggedUsers: list) -> None:
    ...

def get_hashtagID(hashtags: list) -> list:
    conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
    cur = conn.cursor()

    query = "SELECT hashtagID FROM Hashtags WHERE tag_name = ANY(%s);"
    cur.execute(query, (hashtags,))

    hashtag_ids = [row[0] for row in cur.fetchall()]

    return hashtag_ids

def handle_hashtags(postID: int, hashtags: list, postgres: Postgres) -> None:
    if not hashtags:
        return
    # Dump Hashtags in Hashtags table first
    for hashtag in hashtags:
        postgres.load_hashtags_table(hashtag)

    # Preparing for Hashtags_posts storage
    hashtag_ids = get_hashtagID(hashtags)

    postID_hashID = [(postID, hashtag_id) for hashtag_id in hashtag_ids]    
    # Dumping in Hastags_Posts (N:M) table
    postgres.load_posts_hashtags_table(postID_hashID)

def clean_post_data(current_folder: str, influencerID: int) -> None:
    
    data = get_post_dict(current_folder)
    postgres = Postgres() 
    
    for _dict in data:
        _dict = keep_useful_keys(_dict)
        _dict = correct_dtypes_post(_dict)
        _dict['ownerID_TEMP'] = int(influencerID)

        # Loading posts
        postgres.load_posts_table(_dict)
        #postgres.load_brand_posts_table(_dict)
        #handle_mentions(_dict['id'], _dict['mentions'])

        if "taggedUsers" in _dict:
            handle_taggedUsers(_dict["id"], _dict["taggedUsers"])

        if "coauthorProducers" in _dict:
            handle_coauthors(_dict['id'], _dict['coauthorProducers'])

        handle_hashtags(_dict['id'], _dict['hashtags'], postgres)

    postgres.close_connection()

if __name__=="__main__":
    ...