from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.pedagogical_memory import PedagogicalMemory
from app.models.user import User
from app.schemas.chat import ChatMessageOut, ChatRequest, ChatResponse
from app.services.error_analysis import classify_error_heuristic
from app.services.knowledge_base import VectorKnowledgeBase
from app.services.memory import remember as _remember
from app.services.tutor import Tutor

router = APIRouter(prefix="/chat", tags=["chat"])

CONFUSION_KEYWORDS = (
    "pas compris", "comprends pas", "je bloque", "trop difficile",
    "explique autrement", "réexplique", "je suis perdu", "j'ai rien compris",
)
APPRECIATION_KEYWORDS = ("merci", "j'ai compris", "c'est clair", "ok je vois")


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChatResponse:
    document: Optional[Document] = None
    if payload.document_id:
        document = db.get(Document, payload.document_id)
        if document is None or document.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")

    lower = payload.message.lower()
    subject = document.subject if document else ""
    if any(w in lower for w in CONFUSION_KEYWORDS):
        etype = classify_error_heuristic(payload.message, notion="")
        _remember(db, current_user, "confusion", f"Confusion détectée ({etype.value}).\nMessage : {payload.message[:300]}", subject=subject, weight=1.7)
    if any(w in lower for w in APPRECIATION_KEYWORDS):
        _remember(db, current_user, "strategy", f"Approche appréciée suite à : « {payload.message[:200]} ». Réutiliser un style similaire.", subject=subject, weight=1.2)

    chunk_rows = (
        db.query(KnowledgeChunk.document_id, KnowledgeChunk.content)
        .join(Document, Document.id == KnowledgeChunk.document_id)
        .filter(Document.user_id == current_user.id)
        .all()
    )
    knowledge_kb = VectorKnowledgeBase()
    knowledge_kb.build_from_pairs([(row.document_id, row.content) for row in chunk_rows])
    retrieved = knowledge_kb.search(payload.message, top_k=4, document_id=document.id if document else None)

    memory_rows = db.query(PedagogicalMemory).filter(PedagogicalMemory.user_id == current_user.id).order_by(PedagogicalMemory.id.desc()).limit(300).all()
    memory_kb = VectorKnowledgeBase()
    memory_kb.build_from_pairs([(str(m.id), f"[{m.memory_type}] {m.content}") for m in memory_rows])
    pedagogical_snippets = memory_kb.search(payload.message, top_k=5)

    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.document_id == (document.id if document else None))
        .order_by(ChatMessage.id.desc())
        .limit(40)
        .all()
    )
    history = [{"role": "assistant" if m.role == "tutor" else m.role, "content": m.content} for m in reversed(history_rows)]

    tutor = Tutor(api_key=current_user.api_key, api_base=current_user.api_base, model=current_user.model)
    reply = tutor.reply(
        message=payload.message,
        document_text=document.extracted_text if document else None,
        document_title=document.title if document else None,
        retrieved_chunks=retrieved,
        pedagogical_snippets=pedagogical_snippets,
        history=history,
        active_adaptation=None,
    )

    db.add(ChatMessage(user_id=current_user.id, document_id=document.id if document else None, role="user", content=payload.message))
    db.add(ChatMessage(user_id=current_user.id, document_id=document.id if document else None, role="tutor", content=reply))
    db.commit()

    return ChatResponse(reply=reply)


@router.get("/history", response_model=list[ChatMessageOut])
def chat_history(
    document_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.document_id == document_id)
        .order_by(ChatMessage.id)
        .all()
    )
