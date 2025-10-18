from datetime import datetime

def log_db_donfig(message: str) -> None:
    PATH="../logs"
    # Writing to log file
    with open(f"{PATH}/db_config.log", "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] - {message}\n")