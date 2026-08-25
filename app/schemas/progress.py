from typing import Optional

from pydantic import BaseModel


class ProgressOut(BaseModel):
    notion_name: str
    subject: str
    mastery: str
    success: int
    failure: int

    model_config = {"from_attributes": True}


class ProgressResultRequest(BaseModel):
    notion: str
    subject: str
    success: bool
    learner_note: Optional[str] = ""


class ErrorAnalysisOut(BaseModel):
    error_type: str
    summary: str
    strategy: str
    source: str


class ProgressResultResponse(BaseModel):
    progress: ProgressOut
    analysis: Optional[ErrorAnalysisOut] = None
