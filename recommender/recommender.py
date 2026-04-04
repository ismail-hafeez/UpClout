"""Main Recommender class that orchestrates DB, embedding and scoring."""

import json
from typing import Dict, List

from sentence_transformers import util

from db import DBClient
from embedding import Embedder
from utils import load_engagement_csv, get_niche_similarity


class Recommender:
    def __init__(
        self,
        db_client: DBClient = None,
        embedder: Embedder = None,
        engagement_csv: str = "influencer_avg_engagement.csv",
    ):
        self.db = db_client or DBClient()
        self.embedder = embedder or Embedder()
        self.engagement_map = load_engagement_csv(engagement_csv)

    def _attach_engagement_from_csv(self, entities: List[Dict]):
        for e in entities:
            csv_val = self.engagement_map.get(e["id"]) or self.engagement_map.get(
                int(e["id"]), None
            )
            if csv_val is not None:
                try:
                    e["avg_engagement"] = float(csv_val)
                except Exception:
                    e["avg_engagement"] = 0.0

    def _compute_avg_engagement_from_posts(self, entities: List[Dict]):
        # use raw posts (likes, comments) to compute average engagement where possible
        for e in entities:
            posts = e.get("_posts_raw") or []
            engs = []
            for caption, likes, comments in posts:
                if e.get("followers", 0) > 0:
                    # Corrected parenthetical precedence
                    eng = ((likes or 0) + (comments or 0)) / max(1, e.get("followers", 1))
                    engs.append(eng)
            if engs:
                try:
                    e["avg_engagement"] = sum(engs) / len(engs)
                except Exception:
                    e["avg_engagement"] = 0.0

    def build_entities(self):
        influencers = self.db.fetch_influencers()
        brands = self.db.fetch_brands()

        # attach CSV engagement where available
        self._attach_engagement_from_csv(influencers)
        self._attach_engagement_from_csv(brands)

        # compute from posts if not present
        self._compute_avg_engagement_from_posts(influencers)
        self._compute_avg_engagement_from_posts(brands)

        return influencers, brands

    def run(self, out_path: str = "similarity_matches.json"):
        influencers, brands = self.build_entities()

        # prepare texts and embeddings
        brand_texts = [
            self.embedder.prepare_embedding_text(b, is_brand=True) for b in brands
        ]
        influencer_texts = [
            self.embedder.prepare_embedding_text(i, is_brand=False) for i in influencers
        ]

        brand_embeddings = self.embedder.encode(brand_texts, convert_to_tensor=True)
        influencer_embeddings = self.embedder.encode(
            influencer_texts, convert_to_tensor=True
        )

        # semantic search then enhanced scoring
        top10_influencers_for_brand = {}
        for i, brand in enumerate(brands):
            # INCREASED TOP_K TO 100 for better reranking candidates
            top_scores = util.semantic_search(
                brand_embeddings[i : i + 1],
                influencer_embeddings,
                top_k=min(100, len(influencers)),
            )[0]

            enhanced = []
            for hit in top_scores:
                cid = hit["corpus_id"]
                semantic_sim = hit["score"]
                infl = influencers[cid]

                # 1. Niche Similarity (Explicit category boost)
                niche_sim = get_niche_similarity(brand.get("category", ""), infl.get("category", ""))

                # 2. Engagement similarity (normalized)
                eng_diff = abs(brand.get("avg_engagement", 0) - infl.get("avg_engagement", 0))
                engagement_sim = 1 - min(1, eng_diff / max(brand.get("avg_engagement", 0), infl.get("avg_engagement", 0), 1e-6))

                # 3. Follower Tier Similarity (The "Operational Scale" fix)
                # Instead of a pure ratio, we penalize being too far out of tier
                f1 = max(1, brand.get("followers", 1))
                f2 = max(1, infl.get("followers", 1))
                
                # Brands usually want influencers 0.5x to 5x their size
                # High ratio means close in size. 
                ratio = min(f1, f2) / max(f1, f2)
                # Steep penalty if ratio is extremely low (e.g., 1k matching 1M)
                follower_sim = ratio if ratio > 0.01 else ratio * 0.1

                # 4. WEIGHTED SCORE
                # 35% Semantic, 30% Niche, 25% Scale/Tier, 10% Engagement
                score = (semantic_sim * 0.35) + (niche_sim * 0.30) + (follower_sim * 0.25) + (engagement_sim * 0.10)
                enhanced.append((cid, score))

            enhanced.sort(key=lambda x: x[1], reverse=True)
            top10_influencers_for_brand[brand["id"]] = [
                influencers[cid]["id"] for cid, _ in enhanced[:36]
            ]

        top10_brands_for_influencer = {}
        for i, infl in enumerate(influencers):
            top_scores = util.semantic_search(
                influencer_embeddings[i : i + 1],
                brand_embeddings,
                top_k=min(100, len(brands)),
            )[0]

            enhanced = []
            for hit in top_scores:
                cid = hit["corpus_id"]
                semantic_sim = hit["score"]
                brand = brands[cid]

                niche_sim = get_niche_similarity(infl.get("category", ""), brand.get("category", ""))
                
                eng_diff = abs(infl.get("avg_engagement", 0) - brand.get("avg_engagement", 0))
                engagement_sim = 1 - min(1, eng_diff / max(infl.get("avg_engagement", 0), brand.get("avg_engagement", 0), 1e-6))
                
                f1 = max(1, infl.get("followers", 1))
                f2 = max(1, brand.get("followers", 1))
                ratio = min(f1, f2) / max(f1, f2)
                follower_sim = ratio if ratio > 0.01 else ratio * 0.1

                score = (semantic_sim * 0.35) + (niche_sim * 0.30) + (follower_sim * 0.25) + (engagement_sim * 0.10)
                enhanced.append((cid, score))

            enhanced.sort(key=lambda x: x[1], reverse=True)
            top10_brands_for_influencer[infl["id"]] = [
                brands[cid]["id"] for cid, _ in enhanced[:36]
            ]

        results = {
            "top_influencers_for_brand": top10_influencers_for_brand,
            "top_brands_for_influencer": top10_brands_for_influencer,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results

if __name__ == "__main__":
    rec = Recommender()
    results = rec.run()
    print("Done! Results saved to similarity_matches.json")
