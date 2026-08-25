from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.pedagogical_memory import PedagogicalMemory
from app.models.user import User
from app.schemas.memory import MemoryOut

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
def list_memory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PedagogicalMemory]:
    return (
        db.query(PedagogicalMemory)
        .filter(PedagogicalMemory.user_id == current_user.id)
        .order_by(PedagogicalMemory.id.desc())
        .limit(500)
        .all()
    )
