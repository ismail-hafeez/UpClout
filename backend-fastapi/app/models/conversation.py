from pydantic import BaseModel
from typing import Optional


class StartConversationRequest(BaseModel):
    recipientId: str
