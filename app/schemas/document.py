from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DocumentType(str, Enum):
    COURSE = "course"
    EXERCISE = "exercise"
    EXAM = "exam"
    QUIZ = "quiz"
    OTHER = "other"


class DocumentOut(BaseModel):
    id: str
    title: str
    subject: str
    document_type: str
    original_filename: Optional[str]
    extracted_text: str
    has_content: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUpdateText(BaseModel):
    text: str
