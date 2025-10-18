from datetime import datetime

# -- create_database.py -- #
def log_db_donfig(message: str) -> None:
    PATH = "../../logs/db_config"
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