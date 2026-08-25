# EduNova Backend

FastAPI backend for EduNova (documents, OCR, RAG chat, progression tracking).

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Run

    uvicorn app.main:app --reload

## Test

    pytest
