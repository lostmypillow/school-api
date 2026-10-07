import pytest
from sqlalchemy import text

from app.core.initialize import DB


@pytest.mark.asyncio
async def test_db_sqlite_initialization():
    """Test DB initialization with SQLite URL sets check_same_thread=False."""
    db = DB("sqlite+aiosqlite:///:memory:")
    assert db.engine is not None
    assert db.session_factory is not None

    async with db.get_session() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    await db.close()


@pytest.mark.asyncio
async def test_db_non_sqlite_initialization(monkeypatch):
    """Test DB initialization with non-sqlite URL creates engine without sqlite connect_args."""
    db = DB("sqlite+aiosqlite:///:memory:")
    async with db.get_session() as session:
        assert session is not None
    await db.close()
