from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None:
        user = User(username=payload.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    token = create_access_token(user_id=user.id, username=user.username)
    return LoginResponse(token=token, user=user)
