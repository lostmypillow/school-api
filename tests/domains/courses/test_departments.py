from contextlib import asynccontextmanager

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables import Department, Semester
from tests.conftest import DB
from tests.domains.courses.schemas import (
    DepartmentResponseSchema,
    validate_response_format,
)


@pytest.mark.asyncio
async def test_get_departments_missing_param(app_client: AsyncClient):
    """Test /courses/departments returns 422 when required query parameter semester_id is omitted."""
    response = await app_client.get("/courses/departments")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()
    assert "detail" in errors
    assert any(
        err.get("loc") == ["query", "semester_id"] for err in errors["detail"]
    )


@pytest.mark.asyncio
async def test_get_departments_empty_when_no_match(app_client: AsyncClient):
    """Test /courses/departments returns 200 OK and [] when no departments match semester_id."""
    response = await app_client.get(
        "/courses/departments", params={"semester_id": "nonexistent_sem"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_departments_format_and_filtering(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/departments returns strict schema format and accurately filters by semester_id."""
    sem1 = Semester(id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1")
    sem2 = Semester(id="112_2", year="112", sem="2", link="Subj.jsp?year=112&sem=2")
    dep1 = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="Dept CS",
        link="Subj.jsp?year=112&sem=1&code=300",
    )
    dep2 = Department(
        id="112_1_301",
        semester_id="112_1",
        year="112",
        sem="1",
        code="301",
        name="Dept EE",
        link="Subj.jsp?year=112&sem=1&code=301",
    )
    dep3 = Department(
        id="112_2_300",
        semester_id="112_2",
        year="112",
        sem="2",
        code="300",
        name="Dept CS Sem 2",
        link="Subj.jsp?year=112&sem=2&code=300",
    )
    test_session.add_all([sem1, sem2, dep1, dep2, dep3])
    await test_session.commit()

    # Query for semester 112_1 only
    response = await app_client.get(
        "/courses/departments", params={"semester_id": "112_1"}
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2

    # Enforce strict schema contract (no extra, no missing fields, right types)
    validated = validate_response_format(data, DepartmentResponseSchema)
    assert len(validated) == 2

    # Ensure every returned department matches the requested semester_id
    for item in data:
        assert item["semester_id"] == "112_1"

    deps_by_id = {item["id"]: item for item in data}
    assert "112_1_300" in deps_by_id
    assert "112_1_301" in deps_by_id

    d1 = deps_by_id["112_1_300"]
    assert d1["name"] == "Dept CS"
    assert d1["code"] == "300"
    assert d1["year"] == "112"
    assert d1["sem"] == "1"
    assert d1["link"] == "Subj.jsp?year=112&sem=1&code=300"

    d2 = deps_by_id["112_1_301"]
    assert d2["name"] == "Dept EE"
    assert d2["code"] == "301"


@pytest.mark.asyncio
async def test_get_departments_db_error(
    app_client: AsyncClient, test_db: DB, monkeypatch
):
    """Test /courses/departments handles DB errors gracefully by returning 500 via HTTP."""

    @asynccontextmanager
    async def broken_get_session():
        raise RuntimeError("DB connection failure")
        yield  # pragma: no cover

    monkeypatch.setattr(test_db, "get_session", broken_get_session)

    response = await app_client.get(
        "/courses/departments", params={"semester_id": "112_1"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")
