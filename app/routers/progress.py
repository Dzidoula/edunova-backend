from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.pedagogical_memory import PedagogicalMemory
from app.models.progress import Progress
from app.models.user import User
from app.schemas.progress import ErrorAnalysisOut, ProgressOut, ProgressResultRequest, ProgressResultResponse
from app.services.error_analysis import ERROR_LABELS
from app.services.mastery import compute_mastery
from app.services.tutor import Tutor

router = APIRouter(prefix="/progress", tags=["progress"])


def _remember(db: Session, user: User, memory_type: str, content: str, subject: str, notion: str, weight: float) -> None:
    db.add(PedagogicalMemory(user_id=user.id, memory_type=memory_type, subject=subject, notion=notion, content=content[:2000], weight=weight))


@router.get("", response_model=list[ProgressOut])
def list_progress(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Progress]:
    return db.query(Progress).filter(Progress.user_id == current_user.id).order_by(Progress.notion_name).all()


@router.post("/result", response_model=ProgressResultResponse)
def record_result(
    payload: ProgressResultRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressResultResponse:
    entry = (
        db.query(Progress)
        .filter(Progress.user_id == current_user.id, Progress.notion_name == payload.notion)
        .one_or_none()
    )
    if entry is None:
        entry = Progress(user_id=current_user.id, notion_name=payload.notion, subject=payload.subject, success=0, failure=0)
        db.add(entry)

    if payload.success:
        entry.success += 1
    else:
        entry.failure += 1
    entry.mastery = compute_mastery(entry.success, entry.failure)

    analysis_out = None
    if payload.success:
        _remember(
            db, current_user, "success",
            f"L'élève a réussi un exercice sur « {payload.notion} ». Consolider cette notion.",
            subject=payload.subject, notion=payload.notion, weight=1.0,
        )
    else:
        tutor = Tutor(api_key=current_user.api_key, api_base=current_user.api_base, model=current_user.model)
        analysis = tutor.analyze_error(
            message=payload.learner_note or f"Échec sur {payload.notion}",
            notion=payload.notion,
            subject=payload.subject,
            learner_work=payload.learner_note or "",
        )
        _remember(db, current_user, "error", analysis.as_memory_text(), subject=payload.subject, notion=payload.notion, weight=2.0)
        _remember(
            db, current_user, "adaptation",
            f"Pour « {payload.notion} », appliquer : {ERROR_LABELS[analysis.error_type]}. {analysis.summary}",
            subject=payload.subject, notion=payload.notion, weight=1.5,
        )
        analysis_out = ErrorAnalysisOut(
            error_type=analysis.error_type.value, summary=analysis.summary, strategy=analysis.strategy, source=analysis.source
        )

    db.commit()
    db.refresh(entry)
    return ProgressResultResponse(progress=entry, analysis=analysis_out)
