from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.legacy import exec_sql as legacy_exec_sql
from app.core.legacy import new_exec_sql
from app.core.legacy.dependecies import get_session_ctx


@pytest.mark.asyncio
async def test_exec_sql_file_not_found(test_session: AsyncSession):
    """Test legacy exec_sql raises FileNotFoundError when SQL file does not exist."""
    with pytest.raises(FileNotFoundError):
        await legacy_exec_sql.exec_sql(
            mode="all",
            command_name="non_existent_sql_file_12345",
            session=test_session,
        )


@pytest.mark.asyncio
async def test_exec_sql_commit_mode(monkeypatch, test_session: AsyncSession):
    """Test legacy exec_sql mode='commit' executes SQL and commits."""
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value="UPDATE table SET x = 1")

    class MockAsyncContext:
        async def __aenter__(self):
            return mock_file

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("anyio.Path.is_file", lambda self: True)
    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    monkeypatch.setattr("anyio.open_file", AsyncMock(return_value=MockAsyncContext()))

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    result = await legacy_exec_sql.exec_sql(
        mode="commit",
        command_name="update_query",
        session=mock_session,
    )
    assert result is None
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_exec_sql_one_mode(monkeypatch):
    """Test legacy exec_sql mode='one' returns single row dict."""
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value="SELECT 1 AS num")

    class MockAsyncContext:
        async def __aenter__(self):
            return mock_file

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    monkeypatch.setattr("anyio.open_file", AsyncMock(return_value=MockAsyncContext()))

    mock_row = MagicMock()
    mock_row._mapping = {"num": 1}

    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await legacy_exec_sql.exec_sql(
        mode="one",
        command_name="get_one",
        session=mock_session,
    )
    assert result == {"num": 1}


@pytest.mark.asyncio
async def test_exec_sql_all_mode(monkeypatch):
    """Test legacy exec_sql mode='all' returns list of row dicts."""
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value="SELECT * FROM table")

    class MockAsyncContext:
        async def __aenter__(self):
            return mock_file

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    monkeypatch.setattr("anyio.open_file", AsyncMock(return_value=MockAsyncContext()))

    mock_row1 = MagicMock()
    mock_row1._mapping = {"id": 1, "name": "Alice"}
    mock_row2 = MagicMock()
    mock_row2._mapping = {"id": 2, "name": "Bob"}

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row1, mock_row2]

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await legacy_exec_sql.exec_sql(
        mode="all",
        command_name="get_all",
        session=mock_session,
    )
    assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


@pytest.mark.asyncio
async def test_exec_sql_error_propagation(monkeypatch):
    """Test legacy exec_sql re-raises SQLAlchemyError."""
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value="INVALID SQL")

    class MockAsyncContext:
        async def __aenter__(self):
            return mock_file

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    monkeypatch.setattr("anyio.open_file", AsyncMock(return_value=MockAsyncContext()))

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute.side_effect = SQLAlchemyError("Database syntax error")

    with pytest.raises(SQLAlchemyError):
        await legacy_exec_sql.exec_sql(
            mode="all",
            command_name="bad_query",
            session=mock_session,
        )


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug in new_exec_sql.py: mode='one' executes `await result.fetchone().mappings().first()` which raises AttributeError/TypeError",
    strict=True,
)
async def test_new_exec_sql_one_mode_bug(monkeypatch):
    """Edge Case: Calling new_exec_sql mode='one'.

    Bug: `result.fetchone()` returns a Row which has no `.mappings()` method, and is not awaitable.
    """
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value="SELECT 1")

    class MockAsyncContext:
        async def __aenter__(self):
            return mock_file

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    monkeypatch.setattr("anyio.open_file", AsyncMock(return_value=MockAsyncContext()))

    mock_result = MagicMock()
    mock_result.fetchone.return_value = MagicMock()

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    await new_exec_sql.exec_sql(
        mode="one",
        command_name="query",
        session=mock_session,
    )


@pytest.mark.asyncio
async def test_dependencies_get_session_ctx(monkeypatch):
    """Test legacy dependecies get_session and get_session_ctx."""
    mock_session = MagicMock(spec=AsyncSession)

    class MockAsyncSessionContext:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(
        "app.core.legacy.dependecies.async_session",
        lambda: MockAsyncSessionContext(),
    )

    async with get_session_ctx() as session:
        assert session is mock_session
