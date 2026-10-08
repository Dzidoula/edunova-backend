from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None:
        user = User(username=payload.username, password_hash=hash_password(payload.password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            # Création concurrente du même pseudo : on revient au chemin "compte existant".
            db.rollback()
            user = db.query(User).filter(User.username == payload.username).one()
        else:
            db.refresh(user)
    if not user.password_hash:
        # Compte créé avant l'introduction des mots de passe : le premier login en définit un.
        user.password_hash = hash_password(payload.password)
        db.commit()
    elif not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pseudo ou mot de passe incorrect.")
    token = create_access_token(user_id=user.id, username=user.username)
    return LoginResponse(token=token, user=user)
