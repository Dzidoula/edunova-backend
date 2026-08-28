# EduNova Backend

FastAPI backend for EduNova (documents, OCR, RAG chat, progression tracking).

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    alembic upgrade head

`alembic upgrade head` creates the SQLite schema (`edunova.db`). Without it the app starts
but every request that touches the database fails with `no such table: users` (or similar).
Re-run it after pulling changes that add a new migration.

## Run

    uvicorn app.main:app --reload

## Test

    pytest

## Configuration

All configuration is read from environment variables prefixed with `EDUNOVA_` (see `app/core/config.py`).

| Variable | Description | Default |
| --- | --- | --- |
| `EDUNOVA_SECRET_KEY` | Secret used to sign JWT access tokens. | `dev-secret-change-me` |
| `EDUNOVA_DATABASE_URL` | SQLAlchemy database URL. | `sqlite:///./edunova.db` |
| `EDUNOVA_DEFAULT_API_BASE` | Default LLM API base URL used when a user hasn't configured their own. | `https://api.groq.com/openai/v1` |
| `EDUNOVA_DEFAULT_MODEL` | Default LLM model name used when a user hasn't configured their own. | `openai/gpt-oss-120b` |
| `EDUNOVA_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime, in minutes. | `43200` (30 days) |
| `EDUNOVA_FRONTEND_ORIGIN` | Origin allowed by CORS to call this API. | `http://localhost:5173` |
| `EDUNOVA_UPLOAD_DIR` | Directory where uploaded documents are stored. Resolved to an absolute path at startup regardless of the process's working directory. | `uploads` |

### Security model

This application uses **username-only login with no password** (`POST /auth/login` creates or logs into any account given just a username). It is designed for a **trusted, single-tenant-per-instance or trusted-network deployment** — do not expose it to an untrusted multi-tenant environment, since anyone who knows or guesses a username can log in as that user.

`EDUNOVA_SECRET_KEY` **MUST** be set to a real, random secret in any environment beyond local development. The default value (`dev-secret-change-me`) is publicly known and using it in production allows anyone to forge valid access tokens.
