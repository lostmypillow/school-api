from unittest.mock import MagicMock, patch

from redis import Redis
from rq import Worker

from app.domains.tasks.definitions import bootstrap_mssql_task, scrape_to_parquet_task
from app.worker import run_worker


def test_task_functions_exist_and_callable():
    """Verify standard synchronous RQ tasks are imported and callable."""
    assert callable(scrape_to_parquet_task)
    assert callable(bootstrap_mssql_task)


def test_run_worker():
    """Verify run_worker initializes standard Redis connection, Queue, and Worker."""
    with patch("app.worker.Redis.from_url") as mock_from_url, patch(
        "app.worker.Worker"
    ) as mock_worker_cls:
        mock_conn = MagicMock(spec=Redis)
        mock_from_url.return_value = mock_conn

        mock_worker_instance = MagicMock(spec=Worker)
        mock_worker_cls.return_value = mock_worker_instance

        run_worker()

        mock_from_url.assert_called_once()
        mock_worker_cls.assert_called_once()
        mock_worker_instance.work.assert_called_once()
