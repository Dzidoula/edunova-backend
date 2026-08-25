from datetime import datetime

from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: int
    memory_type: str
    subject: str
    notion: str
    content: str
    weight: float
    created_at: datetime

    model_config = {"from_attributes": True}
