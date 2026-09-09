import logging
import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.omdb.schemas import Movie

logger = logging.getLogger(__name__)
from app.dependencies import get_scrape_client
from app.main import app


@pytest.fixture(autouse=True)
def setup_env_deps():
    real_client = AsyncClient(verify=False)
    app.dependency_overrides[get_scrape_client] = lambda: real_client

    yield

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_movies_success():
    assert os.getenv("OMDB_API_KEY"), (
        "OMDB_API_KEY must be set for live integration testing"
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as ac:
        response = await ac.get("/movies/search/", params={"query": "Batman"})

    assert response.status_code == 200
    raw_payload = response.json()
    movie_data = raw_payload["Search"][0]

    movie = Movie.model_validate(movie_data)
    for field_name, field_info in Movie.model_fields.items():
        actual_value = getattr(movie, field_name)
        assert hasattr(movie, field_name), (
            f"Missing field '{field_name}' on Movie instance"
        )
        if field_info.is_required():
            assert actual_value is not None, (
                f"Field '{field_name}' is required but was None"
            )


@pytest.mark.asyncio
async def test_search_movies_missing_query_param():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/movies/search/")
    assert response.status_code == 422
