from unittest.mock import MagicMock, patch

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.domains.tasks.router import router as tasks_router
from app.domains.tasks.schemas import (
    JobStatusResponse,
    TaskQueueResponse,
)


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(tasks_router)
    mock_queue = MagicMock(spec=Queue)
    mock_redis = MagicMock()
    app.state.rq_queue = mock_queue
    app.state.redis = mock_redis
    return app


@pytest.mark.asyncio
async def test_trigger_scrape_to_parquet_no_body(test_app: FastAPI):
    """Test POST /tasks/scrape-to-parquet enqueues task and returns TaskQueueResponse."""
    mock_job = MagicMock(spec=Job)
    mock_job.id = "mock-scrape-job-123"
    test_app.state.rq_queue.enqueue.return_value = mock_job

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/tasks/scrape-to-parquet")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = TaskQueueResponse.model_validate(data)
    assert validated.status == "Queued"
    assert validated.job_id == "mock-scrape-job-123"


@pytest.mark.asyncio
async def test_trigger_scrape_to_parquet_with_body(test_app: FastAPI):
    """Test POST /tasks/scrape-to-parquet with year and sem payload."""
    mock_job = MagicMock(spec=Job)
    mock_job.id = "mock-scrape-job-456"
    test_app.state.rq_queue.enqueue.return_value = mock_job

    payload = {"year": "113", "sem": "1"}
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/tasks/scrape-to-parquet", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = TaskQueueResponse.model_validate(data)
    assert validated.status == "Queued"
    assert validated.job_id == "mock-scrape-job-456"
    test_app.state.rq_queue.enqueue.assert_called_once()
    assert test_app.state.rq_queue.enqueue.call_args.kwargs == {"year": "113", "sem": "1"}


@pytest.mark.asyncio
async def test_trigger_bootstrap_mssql(test_app: FastAPI):
    """Test POST /tasks/bootstrap-mssql enqueues task and returns TaskQueueResponse."""
    mock_job = MagicMock(spec=Job)
    mock_job.id = "mock-bootstrap-job-789"
    test_app.state.rq_queue.enqueue.return_value = mock_job

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/tasks/bootstrap-mssql")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = TaskQueueResponse.model_validate(data)
    assert validated.status == "Queued"
    assert validated.job_id == "mock-bootstrap-job-789"


@pytest.mark.asyncio
async def test_get_job_status_finished(test_app: FastAPI):
    """Test GET /tasks/status returns finished job result with JobStatusResponse."""
    mock_job = MagicMock()
    mock_job.get_status.return_value = "finished"
    mock_job.result = {"semesters": 10, "departments": 25}

    with patch("app.domains.tasks.router.Job.fetch", return_value=mock_job):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/tasks/status", params={"job_id": "job-123"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = JobStatusResponse.model_validate(data)
    assert validated.job_id == "job-123"
    assert validated.status == "finished"
    assert validated.result == {"semesters": 10, "departments": 25}


@pytest.mark.asyncio
async def test_get_job_status_not_found(test_app: FastAPI):
    """Test GET /tasks/status returns not_found when job does not exist."""
    with patch("app.domains.tasks.router.Job.fetch", side_effect=NoSuchJobError):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/tasks/status", params={"job_id": "nonexistent-job"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = JobStatusResponse.model_validate(data)
    assert validated.job_id == "nonexistent-job"
    assert validated.status == "not_found"
    assert validated.result is None


@pytest.mark.asyncio
async def test_trigger_scrape_to_parquet_enqueue_failure(test_app: FastAPI):
    """Test POST /tasks/scrape-to-parquet returns 500 when queueing fails."""
    test_app.state.rq_queue.enqueue.side_effect = Exception("Queue connection failed")

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/tasks/scrape-to-parquet")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Error occurred. Job not queued"
