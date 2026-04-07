from pydantic import BaseModel
from typing import Optional, List


class DeliverableItem(BaseModel):
    type: str
    status: Optional[str] = "Pending"
    link: Optional[str] = ""


class CollaborationCreateRequest(BaseModel):
    campaignId: str
    influencerId: str
    deliverables: Optional[List[DeliverableItem]] = []
    paymentAmount: float
    currency: Optional[str] = "USD"


class CollaborationStatusRequest(BaseModel):
    status: str


class CollaborationDeliverablesRequest(BaseModel):
    deliverables: List[DeliverableItem]


class CollaborationPaymentRequest(BaseModel):
    status: str
    amount: Optional[float] = None
