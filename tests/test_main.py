from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request, status
from httpx import ASGITransport, AsyncClient

from app.main import health_check, lifespan


@pytest.mark.asyncio
async def test_health_check_success():
    """Test health_check endpoint when req.app.state.db_engine is set."""
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.db_engine = "Engine(mssql+aioodbc://...)"

    response = await health_check(mock_request)
    assert response == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_check_live_app():
    """Test calling GET /health on app configured by lifespan returns 200 OK."""
    mock_db = MagicMock()
    mock_redis = MagicMock()

    test_app = FastAPI()
    test_app.state.db = mock_db
    test_app.state.redis = mock_redis
    test_app.state.rq_redis = mock_redis
    test_app.add_api_route("/health", health_check, methods=["GET"])

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_app_lifespan():
    """Test lifespan enables pooling, creates Redis connection, and tears down on exit."""
    test_app = FastAPI()

    mock_redis = MagicMock()
    mock_redis.close = MagicMock()

    with patch("app.main.PoolingManager") as mock_pool, patch(
        "app.main.Redis.from_url", return_value=mock_redis
    ):
        mock_pool.is_enabled.side_effect = [False, True]

        async with lifespan(test_app):
            assert test_app.state.redis is mock_redis
            assert test_app.state.rq_redis is mock_redis
            mock_pool.enable.assert_called_once_with(max_size=50, idle_timeout=600)

        mock_pool.disable.assert_called_once()
        mock_redis.close.assert_called_once()


