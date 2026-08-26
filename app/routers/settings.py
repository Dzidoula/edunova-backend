from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 4:
        return "sk-...." + api_key
    return "sk-..." + api_key[-4:]


@router.get("", response_model=SettingsOut)
def get_settings_route(current_user: User = Depends(get_current_user)) -> SettingsOut:
    return SettingsOut(
        api_key=_mask_api_key(current_user.api_key),
        api_base=current_user.api_base,
        model=current_user.model,
        ocr_engine=current_user.ocr_engine,
    )


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettingsOut:
    if payload.api_key is not None:
        current_user.api_key = payload.api_key.strip()
    current_user.api_base = payload.api_base.strip()
    current_user.model = payload.model.strip()
    current_user.ocr_engine = payload.ocr_engine.strip()
    db.commit()
    db.refresh(current_user)
    return SettingsOut(
        api_key=_mask_api_key(current_user.api_key),
        api_base=current_user.api_base,
        model=current_user.model,
        ocr_engine=current_user.ocr_engine,
    )
