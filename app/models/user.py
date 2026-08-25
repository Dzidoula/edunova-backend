import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    api_key: Mapped[str] = mapped_column(String(256), default="")
    api_base: Mapped[str] = mapped_column(String(256), default="https://api.groq.com/openai/v1")
    model: Mapped[str] = mapped_column(String(128), default="llama-3.3-70b-versatile")
    ocr_engine: Mapped[str] = mapped_column(String(32), default="auto")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents: Mapped[list["Document"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    progress_entries: Mapped[list["Progress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memories: Mapped[list["PedagogicalMemory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
