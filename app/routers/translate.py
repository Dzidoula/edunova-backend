from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.tutor import Tutor

router = APIRouter(prefix="/translate", tags=["translate"])


@router.post("", response_model=TranslateResponse)
def translate(
    payload: TranslateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TranslateResponse:
    text = payload.text or ""

    if payload.document_id:
        document = db.get(Document, payload.document_id)
        if document is None or document.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
        text = (document.extracted_text or "")[:4000]

    if not text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun texte à traduire.")

    tutor = Tutor(api_key=current_user.api_key, api_base=current_user.api_base, model=current_user.model)
    translation = tutor.translate(text, payload.target_lang)
    return TranslateResponse(translation=translation)
