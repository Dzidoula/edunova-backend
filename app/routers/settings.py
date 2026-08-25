from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings_route(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    current_user.api_key = payload.api_key.strip()
    current_user.api_base = payload.api_base.strip()
    current_user.model = payload.model.strip()
    current_user.ocr_engine = payload.ocr_engine.strip()
    db.commit()
    db.refresh(current_user)
    return current_user
