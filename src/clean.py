import pandas as pd 
import json 
import os, re
import shutil
from datetime import datetime, timezone
from pathlib import Path
import load
import importlib
importlib.reload(load)
from load import Postgres
import psycopg2

"""
This script only cleans data 
EXCEPT
it loads hashtags, mentions, taggedUsers and coauthors into DB
"""

folder_path = "../delete"

def delete_folder(folder_path: str) -> None:
    """
    Deletes folder of scraped Creator/Brand that has been stored in DB
    """
    response: str
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        response=f"{folder_path} deleted successfully."
    else:
        response=f"{folder_path} Folder not found."
    write_to_log_file(response)

def write_to_log_file(message: str) -> None:

    PATH="../logs"
    # Writing to log file
    with open(f"{PATH}/data_cleaning.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001FA00-\U0001FAFF"  # more symbols
        u"\u200d"  # zero width joiner
        u"\ufe0f"  # variation selector
        "]+", 
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def remove_spaces(text: str) -> str:
    # Replace newlines with spaces
    cleaned_text = text.replace('\n', ' ').strip()
    # Remove extra spaces
    cleaned_text = ' '.join(cleaned_text.split())

    return cleaned_text

def clean_bio(df: pd.DataFrame) -> pd.DataFrame:

    bio=df["biography"][0]
    # If bio, send to cleaners
    emojiless_bio = remove_emojis(bio)
    cleaned_bio = remove_spaces(emojiless_bio)

    # Saving file with cleaned bio
    df["biography"] = cleaned_bio

    return df

def extract_location(df: pd.DataFrame) -> pd.DataFrame:
    # Mapping of variations → normalized names
    possible_locations = {
        "islamabad": "islamabad",
        "isb": "islamabad",
        "karachi": "karachi",
        "khi": "karachi",
        "rawalpindi": "rawalpindi",
        "pindi": "rawalpindi",
        "rwp": "rawalpindi",
        "lahore": "lahore",
        "lhr": "lahore",
        "peshawar": "peshawar",
        "psh": "peshawar",
        "psw": "peshawar"
    }

    location = "Nan"
    bio = df["biography"][0].lower()

    # Check for any key from city_map in bio_clean
    for key, city in possible_locations.items():
        if key in bio:
            location = city
            break

    # Saving with cleaned bio
    df["location"] = location

    return df

def correct_dtypes_meta(df: pd.DataFrame) -> pd.DataFrame:

    #cols = ['id', 'fullName', 'username', 'followersCount', 'followsCount', 'postsCount', 'biography', 'verified']
    #df = df[cols]

    df = df.astype({
        'id': int,
        'inputUrl': str,
        'fullName': str,
        'username': str,
        'postsCount': int,
        'biography': str,
        'followersCount' : str,
        'followsCount': int,
        'profilePicUrlHD': str,
        'verified': bool,
        'isBusinessAccount': bool,
        'businessCategoryName': str,
        'location': str
    })

    return df

def clean_meta_data(current_folder: str) -> None:
    """
    look for CSV 
    read with pandas
    convert into relevant datatypes
    bio should be in one line
    check for location (call location function)
    write to log file
    """
    csv_file = None
    for file in os.listdir(current_folder):
        if file.endswith(".csv"):
            csv_file = os.path.join(current_folder, file)
            break
    df = pd.read_csv(csv_file)
    # Cleaning Biography
    df = clean_bio(df)
    # Get location if any
    df = extract_location(df)
    # Assign appropriate dtypes
    df = correct_dtypes_meta(df)

    # Closing file
    df.to_csv(csv_file, index=False)
    
    write_to_log_file(f"{csv_file} Cleaned Successfully")

def get_post_dict(current_folder: str) -> dict:
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

def get_hashtagID(hashtags: list) -> list:
    conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
    cur = conn.cursor()

    query = "SELECT hashtagID FROM Hashtags WHERE tag_name = ANY(%s);"
    cur.execute(query, (hashtags,))

    hashtag_ids = [row[0] for row in cur.fetchall()]

    return hashtag_ids

def handle_hashtags(postID: int, hashtags: list) -> None:
    if not hashtags:
        return
    postgres = Postgres()
    # Dump Hashtags in Hashtags table first
    for hashtag in hashtags:
        postgres.load_hashtags_table(hashtag)

    # Preparing for Hashtags_posts storage
    hashtag_ids = get_hashtagID(hashtags)

    postID_hashID = [(postID, hashtag_id) for hashtag_id in hashtag_ids]    
    # Dumping in Hastags_Posts (N:M) table
    postgres.load_posts_hashtags_table(postID_hashID)

    postgres.close_connection()

def handle_mentions(postID: int, mentions: list) -> None:
    ...

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

def handle_coauthors(postID: int, taggedUsers: list) -> None:
    ...

def clean_post_data(current_folder: str) -> None:
    
    data = get_post_dict(current_folder)
    postgres = Postgres()

    for _dict in data:
        _dict = keep_useful_keys(_dict)
        _dict = correct_dtypes_post(_dict)

        # Loading posts
        postgres.load_posts_table(_dict)
        handle_mentions(_dict['id'], _dict['mentions'])

        if "taggedUsers" in _dict:
            handle_taggedUsers(_dict["id"], _dict["taggedUsers"])

        if "coauthorProducers" in _dict:
            handle_coauthors(_dict['id'], _dict['coauthorProducers'])

        handle_hashtags(_dict['id'], _dict['hashtags'])

    postgres.close_connection()
        
        