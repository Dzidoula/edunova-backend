from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="EduNova API")
app.include_router(auth.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
