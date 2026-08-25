from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, chat, documents, memory, progress, settings, translate

settings_obj = get_settings()

app = FastAPI(title="EduNova API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings_obj.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(progress.router)
app.include_router(settings.router)
app.include_router(translate.router)
app.include_router(memory.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
