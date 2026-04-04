"""Artificial Boost Detection Module

Detects if influencers/brands have artificially boosted followers or
engagement through analysis of engagement patterns and anomalies.

Features:
- Engagement consistency analysis (high variance = suspicious)
- Follower/Following ratio analysis
- Post frequency patterns
- Engagement rate anomalies
- Outputs boost_risk_score (0-1) for recommendation weighting
"""

import json
import os
from datetime import datetime

import pandas as pd
import psycopg2


# ============================================================================
# DATABASE CONNECTION
# ============================================================================
def get_db_connection():
    """Connect to PostgreSQL database"""
    if os.getenv("DATABASE_URL"):
        return psycopg2.connect(os.getenv("DATABASE_URL"))

    return psycopg2.connect(
        database="postgres",
        user="postgres",
        password="1040",
        host="localhost",
        port="5432",
    )

# ============================================================================
# DATA FETCHING FROM DB
# ============================================================================
def fetch_influencers_with_posts():
    """Fetch influencers with their engagement metrics from posts"""
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            i.influencerid,
            i.name,
            i.followers,
            i.following,
            i.postcount,
            i.isverified,
            COALESCE(AVG(p.likescount), 0) as avg_likes,
            COALESCE(AVG(p.commentscount), 0) as avg_comments,
            COUNT(p.postid) as total_posts,
            STDDEV(p.likescount + p.commentscount) as engagement_stddev,
            MIN(p.timestamp) as oldest_post,
            MAX(p.timestamp) as newest_post
        FROM influencers i
        LEFT JOIN posts p ON i.influencerid = p.ownerid
        GROUP BY i.influencerid, i.name, i.followers, i.following,
                 i.postcount, i.isverified
        ORDER BY i.followers DESC
    """

    cur.execute(query)
    cols = [d.name for d in cur.description]
    rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=cols)
    cur.close()
    conn.close()

    return df


def fetch_brands_with_posts():
    """Fetch brands with their engagement metrics from posts"""
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            b.brandid,
            b.name,
            b.followers,
            b.following,
            b.postcount,
            b.isverified,
            COALESCE(AVG(p.likescount), 0) as avg_likes,
            COALESCE(AVG(p.commentscount), 0) as avg_comments,
            COUNT(p.postid) as total_posts,
            STDDEV(p.likescount + p.commentscount) as engagement_stddev,
            MIN(p.timestamp) as oldest_post,
            MAX(p.timestamp) as newest_post
        FROM brands b
        LEFT JOIN posts p ON b.brandid = p.ownerbrandid
        GROUP BY b.brandid, b.name, b.followers, b.following,
                 b.postcount, b.isverified
        ORDER BY b.followers DESC
    """

    cur.execute(query)
    cols = [d.name for d in cur.description]
    rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=cols)
    cur.close()
    conn.close()

    return df


# ============================================================================
# BOOST DETECTION ALGORITHMS
# ============================================================================
def calculate_engagement_rate(likes, comments, followers):
    """Calculate engagement rate"""
    if followers == 0:
        return 0
    return (likes + comments) / followers


def detect_engagement_anomaly(row):
    """
    Detect if engagement has unusual patterns (boost indicator).
    High variance in engagement = suspicious
    """
    if pd.isna(row["engagement_stddev"]) or row["engagement_stddev"] == 0:
        return 0.0

    avg_engagement = row["avg_likes"] + row["avg_comments"]
    if avg_engagement == 0:
        return 0.0

    # Coefficient of variation: stddev / mean
    cv = row["engagement_stddev"] / avg_engagement

    # High CV (>1.5) indicates spiky engagement (artificial boost pattern)
    if cv > 1.5:
        return 0.6
    elif cv > 1.0:
        return 0.4
    elif cv > 0.5:
        return 0.2
    else:
        return 0.0


def detect_follower_ratio_anomaly(row):
    """
    Detect suspicious follower/following ratio
    """
    if row["following"] == 0:
        return 0.0

    ratio = row["followers"] / row["following"]

    if ratio > 1000:  # Extremely high ratio
        return 0.5
    elif ratio < 1:  # Following > followers = suspicious
        return 0.4
    elif 1 <= ratio <= 3:
        return 0.0  # Normal
    elif 3 < ratio <= 10:
        return 0.1
    else:
        return 0.2


def detect_engagement_rate_anomaly(row):
    """
    Detect unusually high or low engagement rates
    """
    avg_engagement = row["avg_likes"] + row["avg_comments"]
    er = calculate_engagement_rate(avg_engagement, 0, row["followers"])

    if er > 0.15:  # >15% engagement = likely artificial
        return 0.7
    elif er > 0.10:  # >10% engagement = suspicious
        return 0.5
    elif er > 0.05:  # >5% engagement = slightly high but possible
        return 0.2
    elif er < 0.001 and row["followers"] > 10000:  # Low for large account
        return 0.3
    else:
        return 0.0


def detect_posting_frequency_anomaly(row):
    """
    Detect sudden posting spikes (artificial boost pattern)
    """
    if pd.isna(row["total_posts"]) or row["total_posts"] == 0:
        return 0.0

    if row["oldest_post"] is None or row["newest_post"] is None:
        return 0.0

    days_active = (row["newest_post"] - row["oldest_post"]).days

    if days_active == 0:
        return 0.5 if row["total_posts"] > 5 else 0.0

    posts_per_day = row["total_posts"] / max(1, days_active)

    if posts_per_day > 3:  # More than 3 posts/day = suspicious
        return 0.6
    elif posts_per_day > 1.5:
        return 0.3
    else:
        return 0.0


def calculate_boost_risk_score(row):
    """
    Composite score: 0-1 indicating likelihood of artificial boost
    Aggregates multiple risk factors with weights
    """
    # Individual risk scores
    engagement_anomaly = detect_engagement_anomaly(row)
    ratio_anomaly = detect_follower_ratio_anomaly(row)
    engagement_rate_anomaly = detect_engagement_rate_anomaly(row)
    frequency_anomaly = detect_posting_frequency_anomaly(row)

    # Weighted average (normalized to 0-1)
    weights = {
        "engagement_anomaly": 0.35,
        "ratio_anomaly": 0.25,
        "engagement_rate_anomaly": 0.25,
        "frequency_anomaly": 0.15,
    }

    total_score = (
        engagement_anomaly * weights["engagement_anomaly"]
        + ratio_anomaly * weights["ratio_anomaly"]
        + engagement_rate_anomaly * weights["engagement_rate_anomaly"]
        + frequency_anomaly * weights["frequency_anomaly"]
    )

    # Verified accounts get slight bonus (reduction in risk)
    if row["isverified"]:
        total_score *= 0.85

    return min(1.0, max(0.0, total_score))


def classify_boost_risk(score):
    """Classify boost risk into categories"""
    if score < 0.2:
        return "Natural"
    elif score < 0.4:
        return "Low Risk"
    elif score < 0.6:
        return "Medium Risk"
    elif score < 0.8:
        return "High Risk"
    else:
        return "Very High Risk"


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================
def analyze_artificial_boost(entity_type="influencer"):
    """
    Analyze influencers or brands for artificial boost indicators

    Args:
        entity_type: 'influencer' or 'brand'

    Returns:
        DataFrame with boost risk scores
    """
    if entity_type.lower() == "influencer":
        df = fetch_influencers_with_posts()
        id_col = "influencerid"
    else:
        df = fetch_brands_with_posts()
        id_col = "brandid"

    # Calculate boost risk score for each entity
    df["boost_risk_score"] = df.apply(calculate_boost_risk_score, axis=1)
    df["boost_risk_category"] = df["boost_risk_score"].apply(classify_boost_risk)

    # Add detail columns for debugging
    df["engagement_anomaly_score"] = df.apply(detect_engagement_anomaly, axis=1)
    df["ratio_anomaly_score"] = df.apply(detect_follower_ratio_anomaly, axis=1)
    df["engagement_rate_anomaly_score"] = df.apply(
        detect_engagement_rate_anomaly, axis=1
    )
    df["frequency_anomaly_score"] = df.apply(detect_posting_frequency_anomaly, axis=1)

    return df


# ============================================================================
# OUTPUT & EXPORT
# ============================================================================
def export_boost_analysis(influencer_df, brand_df, output_path="boost_analysis.json"):
    """Export boost analysis to JSON for integration with recommender"""

    output = {"timestamp": datetime.now().isoformat(), "influencers": [], "brands": []}

    # Add influencers
    for _, row in influencer_df.iterrows():
        avg_eng = calculate_engagement_rate(
            row["avg_likes"], row["avg_comments"], row["followers"]
        )
        output["influencers"].append(
            {
                "id": int(row["influencerid"]),
                "name": row["name"],
                "followers": int(row["followers"]),
                "boost_risk_score": round(float(row["boost_risk_score"]), 4),
                "boost_risk_category": row["boost_risk_category"],
                "avg_engagement_rate": round(float(avg_eng), 6),
            }
        )

    # Add brands
    for _, row in brand_df.iterrows():
        avg_eng = calculate_engagement_rate(
            row["avg_likes"], row["avg_comments"], row["followers"]
        )
        output["brands"].append(
            {
                "id": int(row["brandid"]),
                "name": row["name"],
                "followers": int(row["followers"]),
                "boost_risk_score": round(float(row["boost_risk_score"]), 4),
                "boost_risk_category": row["boost_risk_category"],
                "avg_engagement_rate": round(float(avg_eng), 6),
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Boost analysis exported to {output_path}")
    print(f"  - {len(output['influencers'])} influencers analyzed")
    print(f"  - {len(output['brands'])} brands analyzed")


def export_boost_analysis_csv(
    influencer_df,
    brand_df,
    inf_csv_path="influencer_boost_results.csv",
    brand_csv_path="brand_boost_results.csv",
):
    """Export boost analysis to CSV files"""

    # Prepare influencer CSV
    inf_export = influencer_df[
        [
            "influencerid",
            "name",
            "followers",
            "following",
            "boost_risk_score",
            "boost_risk_category",
            "avg_likes",
            "avg_comments",
            "total_posts",
            "engagement_anomaly_score",
            "ratio_anomaly_score",
            "engagement_rate_anomaly_score",
            "frequency_anomaly_score",
        ]
    ].copy()

    # Calculate engagement rate
    inf_export["avg_engagement_rate"] = inf_export.apply(
        lambda row: calculate_engagement_rate(
            row["avg_likes"], row["avg_comments"], row["followers"]
        ),
        axis=1,
    )

    inf_export = inf_export.rename(
        columns={
            "influencerid": "id",
            "boost_risk_score": "risk_score",
            "boost_risk_category": "risk_category",
            "avg_likes": "avg_likes_per_post",
            "avg_comments": "avg_comments_per_post",
            "total_posts": "posts_in_db",
            "engagement_anomaly_score": "engagement_variance_risk",
            "ratio_anomaly_score": "follower_ratio_risk",
            "engagement_rate_anomaly_score": "unusual_engagement_risk",
            "frequency_anomaly_score": "posting_spike_risk",
        }
    )

    inf_export.to_csv(inf_csv_path, index=False, encoding="utf-8")
    print(f"[SUCCESS] Influencer results exported to {inf_csv_path}")
    print(f"  - {len(inf_export)} influencers")

    # Prepare brand CSV
    brand_export = brand_df[
        [
            "brandid",
            "name",
            "followers",
            "following",
            "boost_risk_score",
            "boost_risk_category",
            "avg_likes",
            "avg_comments",
            "total_posts",
            "engagement_anomaly_score",
            "ratio_anomaly_score",
            "engagement_rate_anomaly_score",
            "frequency_anomaly_score",
        ]
    ].copy()

    # Calculate engagement rate
    brand_export["avg_engagement_rate"] = brand_export.apply(
        lambda row: calculate_engagement_rate(
            row["avg_likes"], row["avg_comments"], row["followers"]
        ),
        axis=1,
    )

    brand_export = brand_export.rename(
        columns={
            "brandid": "id",
            "boost_risk_score": "risk_score",
            "boost_risk_category": "risk_category",
            "avg_likes": "avg_likes_per_post",
            "avg_comments": "avg_comments_per_post",
            "total_posts": "posts_in_db",
            "engagement_anomaly_score": "engagement_variance_risk",
            "ratio_anomaly_score": "follower_ratio_risk",
            "engagement_rate_anomaly_score": "unusual_engagement_risk",
            "frequency_anomaly_score": "posting_spike_risk",
        }
    )

    brand_export.to_csv(brand_csv_path, index=False, encoding="utf-8")
    print(f"[SUCCESS] Brand results exported to {brand_csv_path}")
    print(f"  - {len(brand_export)} brands")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("[INFO] Analyzing influencers for artificial boost...")
    influencer_results = analyze_artificial_boost("influencer")

    print("[INFO] Analyzing brands for artificial boost...")
    brand_results = analyze_artificial_boost("brand")

    # Export to JSON
    export_boost_analysis(influencer_results, brand_results, "boost_analysis.json")

    # Print summary statistics
    print("\n=== INFLUENCER BOOST ANALYSIS SUMMARY ===")
    print(f"Total Influencers: {len(influencer_results)}")
    print("\nBoost Risk Distribution:")
    print(influencer_results["boost_risk_category"].value_counts())
    print(
        f"\nAverage Boost Risk Score: "
        f"{influencer_results['boost_risk_score'].mean():.4f}"
    )
    print(
        f"Median Boost Risk Score: "
        f"{influencer_results['boost_risk_score'].median():.4f}"
    )

    print("\n=== BRAND BOOST ANALYSIS SUMMARY ===")
    print(f"Total Brands: {len(brand_results)}")
    print("\nBoost Risk Distribution:")
    print(brand_results["boost_risk_category"].value_counts())
    print(f"\nAverage Boost Risk Score: {brand_results['boost_risk_score'].mean():.4f}")
    print(f"Median Boost Risk Score: {brand_results['boost_risk_score'].median():.4f}")

    # Show high-risk entities
    print("\n=== HIGH RISK ENTITIES (score > 0.6) ===")
    high_risk_inf = influencer_results[
        influencer_results["boost_risk_score"] > 0.6
    ].sort_values("boost_risk_score", ascending=False)
    if len(high_risk_inf) > 0:
        print("\nInfluencers:")
        for _, row in high_risk_inf.head(10).iterrows():
            print(
                f"  {row['name']}: {row['boost_risk_score']:.4f} "
                f"({row['boost_risk_category']})"
            )

    high_risk_brands = brand_results[
        brand_results["boost_risk_score"] > 0.6
    ].sort_values("boost_risk_score", ascending=False)
    if len(high_risk_brands) > 0:
        print("\nBrands:")
        for _, row in high_risk_brands.head(10).iterrows():
            print(
                f"  {row['name']}: {row['boost_risk_score']:.4f} "
                f"({row['boost_risk_category']})"
            )
