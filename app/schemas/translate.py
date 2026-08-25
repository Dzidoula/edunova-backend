from typing import Optional

from pydantic import BaseModel


class TranslateRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    target_lang: str = "français"


class TranslateResponse(BaseModel):
    translation: str
