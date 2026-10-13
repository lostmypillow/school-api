from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException, Request, status
from httpx import ASGITransport, AsyncClient
from rq.exceptions import NoSuchJobError

from app.domains.tasks.jobs import bootstrap_mssql_task, scrape_to_parquet_task
from app.domains.tasks.router import (
    get_job_status,
    router as tasks_router,
    trigger_bootstrap_mssql,
    trigger_scrape_to_parquet,
)


@pytest.mark.asyncio
async def test_trigger_scrape_to_parquet_success():
    """Test POST /tasks/scrape-to-parquet successfully enqueues scrape_to_parquet job."""
    mock_job = MagicMock()
    mock_job.id = "job_123_parquet"

    mock_queue = MagicMock()
    mock_queue.enqueue = MagicMock(return_value=mock_job)

    app = FastAPI()
    app.include_router(tasks_router)
    app.state.rq_queue = mock_queue

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/tasks/scrape-to-parquet")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "Queued",
            "job_id": "job_123_parquet",
        }
        mock_queue.enqueue.assert_called_once_with(scrape_to_parquet_task)


@pytest.mark.asyncio
async def test_trigger_scrape_to_parquet_failure():
    """Test POST /tasks/scrape-to-parquet raises 500 when enqueue returns None."""
    mock_queue = MagicMock()
    mock_queue.enqueue = MagicMock(return_value=None)

    mock_request = MagicMock(spec=Request)
    mock_request.app.state.rq_queue = mock_queue

    with pytest.raises(HTTPException) as exc_info:
        await trigger_scrape_to_parquet(mock_request)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Error occurred. Job not queued"


@pytest.mark.asyncio
async def test_trigger_bootstrap_mssql_success():
    """Test POST /tasks/bootstrap-mssql successfully enqueues bootstrap_mssql job."""
    mock_job = MagicMock()
    mock_job.id = "job_456_mssql"

    mock_queue = MagicMock()
    mock_queue.enqueue = MagicMock(return_value=mock_job)

    app = FastAPI()
    app.include_router(tasks_router)
    app.state.rq_queue = mock_queue

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/tasks/bootstrap-mssql")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "Queued",
            "job_id": "job_456_mssql",
        }
        mock_queue.enqueue.assert_called_once_with(bootstrap_mssql_task)


@pytest.mark.asyncio
async def test_trigger_bootstrap_mssql_failure():
    """Test POST /tasks/bootstrap-mssql raises 500 when enqueue returns None."""
    mock_queue = MagicMock()
    mock_queue.enqueue = MagicMock(return_value=None)

    mock_request = MagicMock(spec=Request)
    mock_request.app.state.rq_queue = mock_queue

    with pytest.raises(HTTPException) as exc_info:
        await trigger_bootstrap_mssql(mock_request)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Error occurred. Job not queued"


@pytest.mark.asyncio
async def test_get_job_status_not_found(monkeypatch):
    """Test GET /tasks/status returns status='not_found' when job is not found."""
    mock_redis = MagicMock()
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.redis = mock_redis
    mock_request.app.state.rq_redis = mock_redis

    monkeypatch.setattr(
        "rq.job.Job.fetch",
        MagicMock(side_effect=NoSuchJobError("No such job")),
    )

    result = await get_job_status(mock_request, job_id="nonexistent_job")
    assert result == {
        "job_id": "nonexistent_job",
        "status": "not_found",
        "result": None,
    }


@pytest.mark.asyncio
async def test_get_job_status_completed_with_result(monkeypatch):
    """Test GET /tasks/status returns job result when completed."""
    mock_redis = MagicMock()
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.redis = mock_redis
    mock_request.app.state.rq_redis = mock_redis

    mock_job = MagicMock()
    mock_job.get_status.return_value = "finished"
    mock_job.result = "Sync completed in 5.2s"

    monkeypatch.setattr(
        "rq.job.Job.fetch",
        MagicMock(return_value=mock_job),
    )

    result = await get_job_status(mock_request, job_id="job_789")
    assert result == {
        "job_id": "job_789",
        "status": "finished",
        "result": "Sync completed in 5.2s",
    }


@pytest.mark.asyncio
async def test_get_job_status_in_progress_no_info(monkeypatch):
    """Test GET /tasks/status returns status and result=None when job is in-progress."""
    mock_redis = MagicMock()
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.redis = mock_redis
    mock_request.app.state.rq_redis = mock_redis

    mock_job = MagicMock()
    mock_job.get_status.return_value = "started"
    mock_job.result = None

    monkeypatch.setattr(
        "rq.job.Job.fetch",
        MagicMock(return_value=mock_job),
    )

    result = await get_job_status(mock_request, job_id="job_inprogress")
    assert result == {
        "job_id": "job_inprogress",
        "status": "started",
        "result": None,
    }
