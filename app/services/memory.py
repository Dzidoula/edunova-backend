from sqlalchemy.orm import Session

from app.models.pedagogical_memory import PedagogicalMemory
from app.models.user import User


def remember(
    db: Session,
    user: User,
    memory_type: str,
    content: str,
    subject: str = "",
    notion: str = "",
    weight: float = 1.0,
) -> None:
    """Record a pedagogical memory row for the user.

    Does NOT commit — the caller controls transaction boundaries.
    """
    content = (content or "").strip()
    if not content:
        return
    db.add(
        PedagogicalMemory(
            user_id=user.id,
            memory_type=memory_type,
            subject=subject,
            notion=notion,
            content=content[:2000],
            weight=weight,
        )
    )
