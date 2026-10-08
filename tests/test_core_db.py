from unittest.mock import MagicMock, patch

import mssql_python
import pytest

from app.core.db import (
    CONNECT_RETRY_ERRORS,
    connect_with_retry,
    exec_mssql,
    exec_mssql_async,
)


def test_connect_retry_errors_set():
    """Test that CONNECT_RETRY_ERRORS contains expected transient error strings."""
    assert "Timeout expired" in CONNECT_RETRY_ERRORS
    assert "Connection timeout expired" in CONNECT_RETRY_ERRORS
    assert "Communication link failure" in CONNECT_RETRY_ERRORS


def test_mssql_python_connect_with_retry_success():
    """Test connect_with_retry successfully returns connection on first attempt."""
    mock_conn = MagicMock(spec=mssql_python.Connection)
    with patch("mssql_python.connect", return_value=mock_conn) as mock_connect:
        conn = connect_with_retry("Server=localhost;Database=test;")
        assert conn == mock_conn
        mock_connect.assert_called_once_with(
            "Server=localhost;Database=test;",
            attrs_before={mssql_python.SQL_ATTR_LOGIN_TIMEOUT: 5},
        )


def test_mssql_python_connect_with_retry_transient_failure():
    """Test connect_with_retry retries on transient connection error before succeeding."""
    mock_conn = MagicMock(spec=mssql_python.Connection)
    transient_exc = mssql_python.OperationalError("Connection timeout expired", "HYT00")

    with patch(
        "mssql_python.connect", side_effect=[transient_exc, mock_conn]
    ), patch("time.sleep") as mock_sleep:
        conn = connect_with_retry("Server=localhost;Database=test;", max_attempts=3)
        assert conn == mock_conn
        mock_sleep.assert_called_once_with(1)  # 2^(1-1) = 1s delay


def test_mssql_python_connect_with_retry_non_retryable_failure():
    """Test connect_with_retry immediately raises non-retryable error."""
    fatal_exc = mssql_python.OperationalError("Login failed for user 'sa'", "28000")

    with patch("mssql_python.connect", side_effect=fatal_exc):
        with pytest.raises(mssql_python.OperationalError):
            connect_with_retry("Server=localhost;Database=test;")


def test_exec_mssql_empty_conn_str_raises(monkeypatch):
    """Test exec_mssql raises ValueError when DB_URL is empty."""
    monkeypatch.setenv("DB_URL", "")
    with pytest.raises(ValueError, match="conn_str is empty"):
        exec_mssql("upsert_semester")


def test_exec_mssql_create_tables(monkeypatch):
    """Test exec_mssql with create_tables executes DDL statements."""
    monkeypatch.setenv("BOOTSTRAP_URL", "Server=localhost;Database=student_db;")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.core.db.connect_with_retry", return_value=mock_conn):
        res = exec_mssql("create_tables", fetch=False)
        assert res is None
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


def test_exec_mssql_named_command_with_batch(monkeypatch):
    """Test exec_mssql runs named SQL script with batch_params."""
    monkeypatch.setenv("DB_URL", "Server=localhost;Database=student_db;")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.core.db.connect_with_retry", return_value=mock_conn):
        batch = [("112_1", "112", "1", "link")]
        res = exec_mssql("upsert_semester", batch_params=batch)
        assert res is None
        mock_cursor.executemany.assert_called_once()
        mock_conn.commit.assert_called_once()



@pytest.mark.asyncio
async def test_exec_mssql_async_success(monkeypatch):
    """Test exec_mssql_async runs exec_mssql in async worker thread."""
    monkeypatch.setenv("DB_URL", "Server=localhost;Database=student_db;")

    with patch("app.core.db.exec_mssql", return_value=[("112_1", "112")]) as mock_exec:
        result = await exec_mssql_async("upsert_semester", "param1", fetch=True)
        assert result == [("112_1", "112")]
        mock_exec.assert_called_once_with(
            "upsert_semester", "param1", fetch=True, batch_params=None
        )
