from fastapi import FastAPI

from app.routers import auth, documents

app = FastAPI(title="EduNova API")
app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
