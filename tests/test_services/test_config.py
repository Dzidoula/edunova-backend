import os
from app.core.config import get_settings


def test_default_settings(monkeypatch):
    monkeypatch.delenv("EDUNOVA_SECRET_KEY", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.database_url == "sqlite:///./edunova.db"
    assert settings.default_model == "llama-3.3-70b-versatile"


def test_env_override(monkeypatch):
    monkeypatch.setenv("EDUNOVA_SECRET_KEY", "test-secret")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.secret_key == "test-secret"
    get_settings.cache_clear()


def test_upload_dir_is_resolved_to_absolute_path(monkeypatch):
    monkeypatch.setenv("EDUNOVA_UPLOAD_DIR", "relative-uploads")
    get_settings.cache_clear()
    settings = get_settings()
    assert os.path.isabs(settings.upload_dir)
    assert settings.upload_dir.endswith("relative-uploads")
    get_settings.cache_clear()
