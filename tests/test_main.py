from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, status
from httpx import ASGITransport, AsyncClient

from app.main import health_check, lifespan


@pytest.mark.asyncio
async def test_health_check_success():
    """Test health_check endpoint when req.app.state.db_engine is set."""
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.db_engine = "Engine(sqlite+aiosqlite:///:memory:)"

    response = await health_check(mock_request)
    assert response == {"status": "healthy"}


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug in main.py line 59: health_check accesses req.app.state.db_engine instead of req.app.state.db, raising AttributeError on live app",
    strict=True,
)
async def test_health_check_live_app_attribute_error_bug():
    """Edge Case: Calling GET /health on app configured by lifespan.

    Bug: lifespan sets `app.state.db`, but health_check accesses `req.app.state.db_engine` raising AttributeError.
    """
    mock_db = MagicMock()
    mock_redis = MagicMock()

    test_app = FastAPI()
    test_app.state.db = mock_db  # Note: db is set, db_engine is NOT set
    test_app.state.arq_redis = mock_redis
    test_app.add_api_route("/health", health_check, methods=["GET"])

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_app_lifespan():
    """Test lifespan initializes db, creates tables, and tears down connections."""
    test_app = FastAPI()

    mock_conn = MagicMock()
    mock_conn.run_sync = AsyncMock()

    mock_db = MagicMock()
    mock_db.engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db.engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_db.close = AsyncMock()

    mock_redis = MagicMock()
    mock_redis.close = AsyncMock()

    with patch("app.main.DB", return_value=mock_db), patch(
        "app.main.create_pool", AsyncMock(return_value=mock_redis)
    ):
        async with lifespan(test_app):
            assert test_app.state.db is mock_db
            assert test_app.state.arq_redis is mock_redis

        mock_db.close.assert_awaited_once()
        mock_redis.close.assert_awaited_once()
