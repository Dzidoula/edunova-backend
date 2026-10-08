import os
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EDUNOVA_")

    env: str = "development"
    secret_key: str = DEFAULT_SECRET_KEY
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


    @model_validator(mode="after")
    def _require_real_secret_in_production(self) -> "Settings":
        if self.env == "production" and self.secret_key in ("", DEFAULT_SECRET_KEY):
            raise ValueError("EDUNOVA_SECRET_KEY doit être défini en production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
