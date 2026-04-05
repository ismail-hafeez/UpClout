from pydantic import BaseModel
from typing import Optional


class ReviewRequest(BaseModel):
    rating: int
    comment: Optional[str] = ""
