"""Embedding and text preparation utilities."""

from typing import List

from sentence_transformers import SentenceTransformer

from utils import categorize_engagement, categorize_followers


class Embedder:
    """Wraps the SentenceTransformer model and text preparation routines."""

    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)

    def prepare_embedding_text(self, entity: dict, is_brand: bool = False) -> str:
        parts: List[str] = []

        # verified
        if entity.get("verified"):
            parts.append("verified account")

        # location
        if entity.get("location"):
            parts.append(f"location {entity['location']}")

        # 3. Bio, Category, Captions
        if entity.get("bio"):
            parts.append(entity["bio"])
        if entity.get("category"):
            parts.append(f"category {entity['category']}")
        if entity.get("captions"):
            captions_text = " ".join(entity["captions"])
            if captions_text.strip():
                parts.append(captions_text)

        return " ".join([p.strip() for p in parts if p and str(p).strip() != "nan"])

    def encode(self, texts: List[str], convert_to_tensor: bool = True):
        return self.model.encode(texts, convert_to_tensor=convert_to_tensor)

    def encode(self, texts: List[str], convert_to_tensor: bool = True):
        return self.model.encode(texts, convert_to_tensor=convert_to_tensor)
