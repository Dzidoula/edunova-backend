import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EDUNOVA_")

    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./edunova.db"
    default_api_base: str = "https://api.groq.com/openai/v1"
    default_model: str = "openai/gpt-oss-120b"
    access_token_expire_minutes: int = 60 * 24 * 30
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "uploads"

    @field_validator("upload_dir")
    @classmethod
    def _resolve_upload_dir(cls, value: str) -> str:
        return os.path.abspath(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
