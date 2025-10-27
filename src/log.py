from datetime import datetime

# -- create_database.py -- #
def log_db_donfig(message: str) -> None:
    PATH = "../logs/db_config"
    # Writing to log file
    with open(f"{PATH}/create_database.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- load.py -- #
def log_influencer_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/influencer.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_brand_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/brand.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_hashtags_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/hashtags.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_posts_hashtags_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/posts_hashtags.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_posts_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/posts.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_taggedUsers_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/taggedUsers.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_posts_taggedUsers_table(message: str) -> None:
    PATH = "../logs/load"
    # Writing to log file
    with open(f"{PATH}/posts_taggedUsers.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- post_data.py -- #
def log_post_data(message: str) -> None:
    PATH = "../logs/transform"
    # Writing to log file
    with open(f"{PATH}/post_data.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- meta_data.py -- #
def log_meta_data(message: str) -> None:
    PATH = "../logs/transform"
    # Writing to log file
    with open(f"{PATH}/meta_data.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- apify_class.py -- #
def log_extract_meta_data(message: str) -> None:
    PATH = "../logs/extract"
    # Writing to log file
    with open(f"{PATH}/meta_data_scraping.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

def log_extract_post_data(message: str) -> None:
    PATH = "../logs/extract"
    # Writing to log file
    with open(f"{PATH}/post_data_scraping.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- main.py -- #
def log_skipped_influencer(message: str) -> None:
    PATH = "../logs"
    # Writing to log file
    with open(f"{PATH}/skipped_influencer.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- main_brand.py -- #
def log_skipped_brand(message: str) -> None:
    PATH = "../logs"
    # Writing to log file
    with open(f"{PATH}/skipped_brand.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")

# -- apify_class.py -- #
def log_api_usage(message: str) -> None:
    PATH = "../logs/api"
    # Writing to log file
    with open(f"{PATH}/current_api.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")