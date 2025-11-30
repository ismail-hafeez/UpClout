"""
To help detect rising stars
"""

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.load import Postgres

def get_rising_star(postgres: Postgres) -> list:
    """
    Return ID of the influencer with followers less than 100000
    """
    query = """
        SELECT influencerID, username, followers FROM Influencers WHERE followers < 100000;
    """
    postgres.cur.execute(query)
    
    return postgres.cur.fetchall()
    
if __name__ == "__main__":
    postgres = Postgres()
    
    rising_stars = get_rising_star(postgres)
    print(rising_stars)

    postgres.close_connection()