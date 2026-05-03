"""Database access utilities for the recommender."""

import os
from typing import Dict, List

from db_utils import get_connection

DB_URL = os.getenv("DATABASE_URL")


class DBClient:
    """Simple DB client to fetch influencers, brands and posts."""

    def __init__(self):
        pass

    def get_connection(self):
        return get_connection()

    def fetch_influencers(self) -> List[Dict]:
        """Return list of influencer dicts with fields used by recommender."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT influencerid, bio, businesscategoryname, location, isverified, followers
            FROM influencers
            """
        )
        influencers = []
        for infl_id, bio, category, location, verified, followers in cur.fetchall():
            influencers.append(
                {
                    "id": str(infl_id),
                    "bio": bio or "",
                    "category": category or "",
                    "location": location or "",
                    "verified": bool(verified),
                    "followers": int(followers or 0),
                }
            )

        # fetch top posts (caption, likescount, commentscount)
        for infl in influencers:
            cur.execute(
                """
                SELECT caption, likescount, commentscount FROM posts
                WHERE ownerid = %s AND ownerbrandid IS NULL
                ORDER BY timestamp DESC LIMIT 25
                """,
                (int(infl["id"]),),
            )
            posts = cur.fetchall()
            infl["captions"] = [row[0] or "" for row in posts]
            infl["_posts_raw"] = posts

        cur.close()
        conn.close()
        return influencers

    def fetch_brands(self) -> List[Dict]:
        """Return list of brand dicts with fields used by recommender."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT brandid, bio, businesscategoryname, location, isverified, followers
            FROM brands
            """
        )
        brands = []
        for brand_id, bio, category, location, verified, followers in cur.fetchall():
            brands.append(
                {
                    "id": str(brand_id),
                    "bio": bio or "",
                    "category": category or "",
                    "location": location or "",
                    "verified": bool(verified),
                    "followers": int(followers or 0),
                }
            )

        for brand in brands:
            cur.execute(
                """
                SELECT caption, likescount, commentscount FROM posts
                WHERE ownerbrandid = %s AND ownerid IS NULL
                ORDER BY timestamp DESC LIMIT 25
                """,
                (int(brand["id"]),),
            )
            posts = cur.fetchall()
            brand["captions"] = [row[0] or "" for row in posts]
            brand["_posts_raw"] = posts

        cur.close()
        conn.close()
        return brands
        return brands
