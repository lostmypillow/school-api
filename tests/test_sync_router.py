import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException, Request, status
from httpx import ASGITransport, AsyncClient

from app.domains.sync.router import (
    get_job_status,
    router as sync_router,
    trigger_sync_mssql,
    trigger_sync_sqlite,
)


@pytest.mark.asyncio
async def test_trigger_sync_sqlite_success():
    """Test POST /sync/sqlite successfully enqueues bootstrap_sqlite job."""
    mock_job = MagicMock()
    mock_job.job_id = "job_123_sqlite"

    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

    app = FastAPI()
    app.include_router(sync_router)
    app.state.arq_redis = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/sync/sqlite")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "Queued",
            "job_id": "job_123_sqlite",
        }
        mock_pool.enqueue_job.assert_awaited_once_with("bootstrap_sqlite")


@pytest.mark.asyncio
async def test_trigger_sync_sqlite_failure():
    """Test POST /sync/sqlite raises 500 when enqueue_job returns None."""
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=None)

    mock_request = MagicMock(spec=Request)
    mock_request.app.state.arq_redis = mock_pool

    with pytest.raises(HTTPException) as exc_info:
        await trigger_sync_sqlite(mock_request)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Error occurred. Job not queued"


@pytest.mark.asyncio
async def test_trigger_sync_mssql_success():
    """Test POST /sync/mssql successfully enqueues bootstrap_mssql job."""
    mock_job = MagicMock()
    mock_job.job_id = "job_456_mssql"

    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

    app = FastAPI()
    app.include_router(sync_router)
    app.state.arq_redis = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/sync/mssql")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "Queued",
            "job_id": "job_456_mssql",
        }
        mock_pool.enqueue_job.assert_awaited_once_with("bootstrap_mssql")


@pytest.mark.asyncio
async def test_trigger_sync_mssql_failure():
    """Test POST /sync/mssql raises 500 when enqueue_job returns None."""
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=None)

    mock_request = MagicMock(spec=Request)
    mock_request.app.state.arq_redis = mock_pool

    with pytest.raises(HTTPException) as exc_info:
        await trigger_sync_mssql(mock_request)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Error occurred. Job not queued"


@pytest.mark.asyncio
async def test_get_job_status_not_found(monkeypatch):
    """Test GET /sync/status returns status='not_found' when job is not found."""
    mock_pool = MagicMock()
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.arq_redis = mock_pool

    mock_job = MagicMock()
    mock_job.status = AsyncMock(return_value="not_found")

    sync_module = sys.modules[get_job_status.__module__]
    monkeypatch.setattr(sync_module, "Job", lambda jid, pool: mock_job)

    result = await get_job_status(mock_request, job_id="nonexistent_job")
    assert result == {
        "job_id": "nonexistent_job",
        "status": "not_found",
        "result": None,
    }


@pytest.mark.asyncio
async def test_get_job_status_completed_with_result(monkeypatch):
    """Test GET /sync/status returns job result when completed."""
    mock_pool = MagicMock()
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.arq_redis = mock_pool

    mock_info = MagicMock()
    mock_info.result = "Sync completed in 5.2s"

    mock_job = MagicMock()
    mock_job.status = AsyncMock(return_value="complete")
    mock_job.result_info = AsyncMock(return_value=mock_info)

    sync_module = sys.modules[get_job_status.__module__]
    monkeypatch.setattr(sync_module, "Job", lambda jid, pool: mock_job)

    result = await get_job_status(mock_request, job_id="job_789")
    assert result == {
        "job_id": "job_789",
        "status": "complete",
        "result": "Sync completed in 5.2s",
    }


@pytest.mark.asyncio
async def test_get_job_status_in_progress_no_info(monkeypatch):
    """Test GET /sync/status returns status and result=None when job is in-progress."""
    mock_pool = MagicMock()
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.arq_redis = mock_pool

    mock_job = MagicMock()
    mock_job.status = AsyncMock(return_value="in_progress")
    mock_job.result_info = AsyncMock(return_value=None)

    sync_module = sys.modules[get_job_status.__module__]
    monkeypatch.setattr(sync_module, "Job", lambda jid, pool: mock_job)

    result = await get_job_status(mock_request, job_id="job_inprogress")
    assert result == {
        "job_id": "job_inprogress",
        "status": "in_progress",
        "result": None,
    }
