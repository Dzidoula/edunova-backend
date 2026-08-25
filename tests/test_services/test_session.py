from sqlalchemy import text

from app.db.session import get_db


def test_get_db_yields_working_session():
    gen = get_db()
    db = next(gen)
    result = db.execute(text("SELECT 1")).scalar()
    assert result == 1
    gen.close()
