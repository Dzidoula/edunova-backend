from pydantic import BaseModel


class SettingsOut(BaseModel):
    api_key: str
    api_base: str
    model: str
    ocr_engine: str

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    api_key: str
    api_base: str
    model: str
    ocr_engine: str
