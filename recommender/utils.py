"""Utility helpers used across recommender modules."""

from typing import Dict


def categorize_followers(count: int) -> str:
    if count > 1_000_000:
        return "very high followers"
    if count > 100_000:
        return "high followers"
    if count > 10_000:
        return "medium followers"
    return "low followers"


def get_niche_similarity(cat1: str, cat2: str) -> float:
    """Calculate similarity between two category strings based on predefined groups."""
    c1, c2 = cat1.lower(), cat2.lower()
    if not c1 or not c2: return 0.0
    if c1 == c2: return 1.0
    
    groups = [
        ["clothing", "apparel", "accessories", "jewelry", "fashion", "shopping", "retail"],
        ["food", "beverage", "restaurant", "cafe", "bakery", "kitchen", "cooking"],
        ["beauty", "cosmetics", "personal care", "hair", "skincare", "makeup"],
        ["fitness", "gym", "health", "wellness", "sports", "coach"],
        ["lifestyle", "blogger", "digital creator", "influencer", "public figure"],
        ["technology", "electronics", "software", "app", "science"],
        ["travel", "hotel", "tourism", "adventure"],
        ["home", "decor", "furniture", "design", "real estate"]
    ]
    
    for g in groups:
        if any(keyword in c1 for keyword in g) and any(keyword in c2 for keyword in g):
            return 0.8
            
    return 0.0

def categorize_engagement(rate: float) -> str:
    if rate > 0.5:
        return "very high engagement"
    if rate > 0.1:
        return "high engagement"
    if rate > 0.01:
        return "medium engagement"
    return "low engagement"


def load_engagement_csv(path: str) -> Dict[str, float]:
    """Load CSV with columns id,avg_engagement_rate into dict.
    This function avoids heavy imports for the top-level modules; callers
    may use pandas directly if available."""
    try:
        import pandas as pd

        df = pd.read_csv(path)
        return {str(r[0]): float(r[1]) for r in df.values}
    except Exception:
        return {}
