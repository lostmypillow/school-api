from contextlib import asynccontextmanager

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables import Department, DepartmentYear, Semester
from tests.conftest import DB
from tests.domains.courses.schemas import (
    DepartmentYearResponseSchema,
    validate_response_format,
)


@pytest.mark.asyncio
async def test_get_department_years_missing_param(app_client: AsyncClient):
    """Test /courses/department_years returns 422 when department_id query parameter is omitted."""
    response = await app_client.get("/courses/department_years")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()
    assert "detail" in errors
    assert any(
        err.get("loc") == ["query", "department_id"] for err in errors["detail"]
    )


@pytest.mark.asyncio
async def test_get_department_years_empty_when_no_match(app_client: AsyncClient):
    """Test /courses/department_years returns 200 OK and [] when department_id has no matches."""
    response = await app_client.get(
        "/courses/department_years", params={"department_id": "nonexistent_dept"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_department_years_format_and_filtering(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/department_years returns strict schema format and accurately filters by department_id."""
    sem = Semester(id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1")
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
    dy1 = DepartmentYear(
        id="112_1_300_101",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="101",
        name="CS Year 1",
        link="Subj.jsp?year=112&sem=1&code=101",
    )
    dy2 = DepartmentYear(
        id="112_1_300_102",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="102",
        name="CS Year 2",
        link="Subj.jsp?year=112&sem=1&code=102",
    )
    dy_other = DepartmentYear(
        id="112_1_301_201",
        department_id="112_1_301",
        year="112",
        sem="1",
        code="201",
        name="EE Year 1",
        link="Subj.jsp?year=112&sem=1&code=201",
    )
    test_session.add_all([sem, dep1, dep2, dy1, dy2, dy_other])
    await test_session.commit()

    response = await app_client.get(
        "/courses/department_years", params={"department_id": "112_1_300"}
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2

    # Enforce strict schema contract (no extra, no missing fields, right types)
    validated = validate_response_format(data, DepartmentYearResponseSchema)
    assert len(validated) == 2

    # Verify filtering ensures all items belong to 112_1_300
    for item in data:
        assert item["department_id"] == "112_1_300"

    years_by_id = {item["id"]: item for item in data}
    assert "112_1_300_101" in years_by_id
    assert "112_1_300_102" in years_by_id

    y1 = years_by_id["112_1_300_101"]
    assert y1["name"] == "CS Year 1"
    assert y1["code"] == "101"
    assert y1["year"] == "112"
    assert y1["sem"] == "1"
    assert y1["link"] == "Subj.jsp?year=112&sem=1&code=101"

    y2 = years_by_id["112_1_300_102"]
    assert y2["name"] == "CS Year 2"
    assert y2["code"] == "102"


@pytest.mark.asyncio
async def test_get_department_years_db_error(
    app_client: AsyncClient, test_db: DB, monkeypatch
):
    """Test /courses/department_years handles DB errors by returning 500 via HTTP."""

    @asynccontextmanager
    async def broken_get_session():
        raise RuntimeError("DB error")
        yield  # pragma: no cover

    monkeypatch.setattr(test_db, "get_session", broken_get_session)

    response = await app_client.get(
        "/courses/department_years", params={"department_id": "112_1_300"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")
