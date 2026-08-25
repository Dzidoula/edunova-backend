import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import get_current_user
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentUpdateText
from app.services.knowledge_base import chunk_text
from app.services.text_extraction import extract_text_from_file

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


def _reindex(db: Session, document: Document) -> None:
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).delete()
    for i, content in enumerate(chunk_text(document.extracted_text or "")):
        db.add(KnowledgeChunk(document_id=document.id, chunk_index=i, content=content))
    db.commit()


def _save_upload(user_id: str, upload: UploadFile) -> str:
    settings = get_settings()
    user_dir = os.path.join(settings.upload_dir, user_id)
    os.makedirs(user_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4()}_{upload.filename}"
    dest = os.path.join(user_dir, safe_name)
    with open(dest, "wb") as f:
        f.write(upload.file.read())
    return dest


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    title: str = Form(...),
    subject: str = Form(...),
    document_type: str = Form(...),
    text_override: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    file_path = None
    original_filename = None
    text = ""

    if file is not None:
        file_path = _save_upload(current_user.id, file)
        original_filename = file.filename
        text, _method = extract_text_from_file(file_path, use_ocr_if_needed=True, ocr_engine=current_user.ocr_engine)

    if text_override and text_override.strip():
        text = text_override.strip()

    document = Document(
        user_id=current_user.id,
        title=title,
        subject=subject,
        document_type=document_type,
        original_filename=original_filename,
        file_path=file_path,
        extracted_text=text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    _reindex(db, document)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


def _get_owned_document(db: Session, document_id: str, user: User) -> Document:
    document = db.get(Document, document_id)
    if document is None or document.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
    return document


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Document:
    return _get_owned_document(db, document_id, current_user)


@router.put("/{document_id}/text", response_model=DocumentOut)
def update_document_text(
    document_id: str,
    payload: DocumentUpdateText,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    document = _get_owned_document(db, document_id, current_user)
    document.extracted_text = payload.text
    db.commit()
    db.refresh(document)
    _reindex(db, document)
    return document


@router.post("/{document_id}/ocr", response_model=DocumentOut)
def rerun_ocr(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Document:
    document = _get_owned_document(db, document_id, current_user)
    if not document.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun fichier source à relire en OCR.")
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier source est introuvable sur le serveur.")
    text, _method = extract_text_from_file(document.file_path, use_ocr_if_needed=True, ocr_engine=current_user.ocr_engine)
    if text.strip():
        document.extracted_text = text
        db.commit()
        db.refresh(document)
        _reindex(db, document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    document = _get_owned_document(db, document_id, current_user)
    file_path = document.file_path
    db.delete(document)
    db.commit()
    if file_path:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            logger.warning("Failed to remove upload file %s: %s", file_path, e)
