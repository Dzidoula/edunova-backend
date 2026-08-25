from fastapi import FastAPI

app = FastAPI(title="EduNova API")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
