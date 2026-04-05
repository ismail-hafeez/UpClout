from pydantic import BaseModel
from typing import Optional


class CampaignCreateRequest(BaseModel):
    title: str
    goal: str
    budget: float
    niche: Optional[str] = ""
    timeline: Optional[str] = ""


class CampaignStatusRequest(BaseModel):
    status: str
