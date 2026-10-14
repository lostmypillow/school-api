from contextlib import asynccontextmanager

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables import Semester
from tests.conftest import DB
from tests.domains.courses.schemas import SemesterResponseSchema, validate_response_format


@pytest.mark.asyncio
async def test_get_semesters_empty(app_client: AsyncClient):
    """Test /courses/semesters returns 200 OK and an empty list when no data exists."""
    response = await app_client.get("/courses/semesters")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_semesters_format_and_values(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/semesters returns valid schema format and accurate semester records."""
    sem1 = Semester(id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1")
    sem2 = Semester(id="112_2", year="112", sem="2", link="Subj.jsp?year=112&sem=2")
    test_session.add_all([sem1, sem2])
    await test_session.commit()

    response = await app_client.get("/courses/semesters")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2

    # Enforce strict schema contract (all fields, correct types, no missing or extra fields)
    validated = validate_response_format(data, SemesterResponseSchema)
    assert len(validated) == 2

    # Verify field values match seeded records exactly
    semesters_by_id = {item["id"]: item for item in data}
    assert "112_1" in semesters_by_id
    assert "112_2" in semesters_by_id

    s1 = semesters_by_id["112_1"]
    assert s1["year"] == "112"
    assert s1["sem"] == "1"
    assert s1["link"] == "Subj.jsp?year=112&sem=1"
    assert isinstance(s1["created_at"], str)
    assert isinstance(s1["updated_at"], str)

    s2 = semesters_by_id["112_2"]
    assert s2["year"] == "112"
    assert s2["sem"] == "2"
    assert s2["link"] == "Subj.jsp?year=112&sem=2"


@pytest.mark.asyncio
async def test_get_semesters_db_error(
    app_client: AsyncClient, test_db: DB, monkeypatch
):
    """Test /courses/semesters endpoint logic catches DB error and returns 500 via HTTP."""

    @asynccontextmanager
    async def broken_get_session():
        raise RuntimeError("Database connection lost")
        yield  # pragma: no cover

    monkeypatch.setattr(test_db, "get_session", broken_get_session)

    response = await app_client.get("/courses/semesters")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")
