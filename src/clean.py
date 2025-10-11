import pandas as pd 
import json 
import os, re
import shutil
from datetime import datetime
from pathlib import Path

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
    bio = df["biography"][0]

    # Check for any key from city_map in bio_clean
    for key, city in possible_locations.items():
        if key in bio:
            location = city
            break

    # Saving with cleaned bio
    df["location"] = location

    return df

def correct_dtypes(df: pd.DataFrame) -> pd.DataFrame:

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
    df = correct_dtypes(df)

    # Closing file
    df.to_csv(csv_file, index=False)
    
    write_to_log_file(f"{csv_file} Cleaned Successfully")

def clean_post_data(current_folder: str): # -> Generator
    json_file = None
    for file in os.listdir(current_folder):
        if file.endswith(".json"):
            json_file = os.path.join(current_folder, file)
            break

    with open(json_file, "r", encoding="utf-8") as file:
        data=json.load(file)
   
    for _dict in data:
        yield _dict

