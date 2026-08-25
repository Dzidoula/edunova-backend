import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_all_tables(tmp_path):
    db_path = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_path}"

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parent.parent,
        env={"EDUNOVA_DATABASE_URL": db_url, "PATH": "/usr/bin:/bin"},
        check=True,
    )

    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    expected = {
        "users",
        "documents",
        "knowledge_chunks",
        "chat_messages",
        "progress",
        "pedagogical_memories",
    }
    assert expected.issubset(tables)
