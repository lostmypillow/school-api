from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.courses.bootstrap_mssql import bootstrap_mssql
from app.domains.courses.bootstrap_sqlite import bootstrap_sqlite
from app.worker import WorkerSettings, shutdown, startup


@pytest.mark.asyncio
async def test_worker_settings():
    """Test WorkerSettings configuration values."""
    assert WorkerSettings.functions == [bootstrap_sqlite, bootstrap_mssql]
    assert WorkerSettings.max_jobs == 10
    assert WorkerSettings.job_timeout == 3000
    assert WorkerSettings.on_startup == startup
    assert WorkerSettings.on_shutdown == shutdown


@pytest.mark.asyncio
async def test_worker_startup_database_creation():
    """Test startup checks for student_db existence and creates it if missing."""
    ctx = {}

    mock_bootstrap_conn = MagicMock()
    mock_bootstrap_conn.execution_options = AsyncMock(return_value=mock_bootstrap_conn)
    mock_result = MagicMock()
    mock_result.scalar.return_value = None  # DB does not exist
    mock_bootstrap_conn.execute = AsyncMock(return_value=mock_result)

    mock_bootstrap_engine = MagicMock()
    mock_bootstrap_engine.connect.return_value.__aenter__ = AsyncMock(
        return_value=mock_bootstrap_conn
    )
    mock_bootstrap_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_bootstrap_engine.dispose = AsyncMock()

    with patch("app.worker.DB") as mock_db_class:
        mock_db_instance = MagicMock()
        mock_db_instance.engine = mock_bootstrap_engine
        mock_db_class.return_value = mock_db_instance

        await startup(ctx)

        assert "database" in ctx
        assert "mssql_db" in ctx
        assert "client" in ctx
        assert ctx["client"] is not None

        # Clean up client
        await ctx["client"].aclose()


@pytest.mark.asyncio
async def test_worker_shutdown():
    """Test shutdown disposes all database connections and closes HTTP client."""
    mock_sqlite = MagicMock()
    mock_sqlite.close = AsyncMock()

    mock_mssql = MagicMock()
    mock_mssql.close = AsyncMock()

    mock_client = MagicMock()
    mock_client.is_closed = False
    mock_client.aclose = AsyncMock()

    ctx = {
        "database": mock_sqlite,
        "mssql_db": mock_mssql,
        "client": mock_client,
    }

    await shutdown(ctx)

    mock_sqlite.close.assert_awaited_once()
    mock_mssql.close.assert_awaited_once()
    mock_client.aclose.assert_awaited_once()
    assert ctx["client"] is None
