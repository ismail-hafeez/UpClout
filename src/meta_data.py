import pandas as pd 
import os, re
import log

def remove_emojis(text: str) -> str:
    # Decode bytes to string if needed
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
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
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')

    cleaned_text = text.replace('\n', ' ').strip()
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text

def clean_bio(df: pd.DataFrame) -> pd.DataFrame:
    # Extract biography safely
    bio = df.get("biography", [None])[0]

    # Handle None, empty, or non-string values
    if not bio or not isinstance(bio, (str, bytes)):
        df["biography"] = ""
        return df

    # If it's bytes, decode to UTF-8
    if isinstance(bio, bytes):
        bio = bio.decode("utf-8", errors="ignore")

    try:
        # Clean emoji and spaces
        emojiless_bio = remove_emojis(bio)
        cleaned_bio = remove_spaces(emojiless_bio)
        df["biography"] = cleaned_bio
    except Exception as e:
        print(f"Error cleaning bio: {e}")
        df["biography"] = bio 

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

def clean_meta_data(current_folder: str) -> int:
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
    
    log.log_meta_data(f"{csv_file} Cleaned Successfully")

    return int(df['id'][0])


        
        