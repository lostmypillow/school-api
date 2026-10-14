from contextlib import asynccontextmanager

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables import Course, Department, DepartmentYear, Semester
from tests.conftest import DB
from tests.domains.courses.schemas import CourseResponseSchema, validate_response_format


@pytest.mark.asyncio
async def test_get_courses_missing_param(app_client: AsyncClient):
    """Test /courses/courses returns 422 when department_year_id query parameter is omitted."""
    response = await app_client.get("/courses/courses")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()
    assert "detail" in errors
    assert any(
        err.get("loc") == ["query", "department_year_id"]
        for err in errors["detail"]
    )


@pytest.mark.asyncio
async def test_get_courses_empty_when_no_match(app_client: AsyncClient):
    """Test /courses/courses returns 200 OK and [] when department_year_id has no matches."""
    response = await app_client.get(
        "/courses/courses", params={"department_year_id": "nonexistent_dy"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_courses_format_and_filtering(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/courses returns strict schema format and accurately filters by department_year_id."""
    sem = Semester(id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1")
    dep = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="Dept CS",
        link="Subj.jsp?year=112&sem=1&code=300",
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
    # Course with full optional fields populated
    c1 = Course(
        id="112_1_101_300001",
        department_year_id="112_1_300_101",
        year="112",
        sem="1",
        code="300001",
        name="Algorithms",
        link="Subj.jsp?course=300001",
        credits=3,
        course_type="Required",
        instructor="Prof Turing",
        sun=None,
        mon="1-3",
        tue=None,
        wed="2-4",
        thu=None,
        fri=None,
        sat=None,
        classroom="Room 404",
        students_enrolled=50,
        students_dropped=2,
        language="English",
        notes="Prerequisite: Data Structures",
        with_class="CS-A",
        experiment="Lab 1",
        cross_discipline="No",
    )
    # Course with optional fields left as None
    c2 = Course(
        id="112_1_101_300002",
        department_year_id="112_1_300_101",
        year="112",
        sem="1",
        code="300002",
        name="Data Structures",
        credits=3,
        instructor="Prof Knuth",
        classroom="Room 405",
        students_enrolled=45,
        students_dropped=0,
    )
    # Course belonging to another department year
    c_other = Course(
        id="112_1_102_300003",
        department_year_id="112_1_300_102",
        year="112",
        sem="1",
        code="300003",
        name="Operating Systems",
        credits=3,
        instructor="Prof Dijkstra",
    )
    test_session.add_all([sem, dep, dy1, dy2, c1, c2, c_other])
    await test_session.commit()

    response = await app_client.get(
        "/courses/courses", params={"department_year_id": "112_1_300_101"}
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2

    # Enforce strict schema contract (all 27 fields validated, no extra, no missing fields)
    validated = validate_response_format(data, CourseResponseSchema)
    assert len(validated) == 2

    # Ensure all returned items match the requested department_year_id
    for item in data:
        assert item["department_year_id"] == "112_1_300_101"

    courses_by_id = {c["id"]: c for c in data}
    assert "112_1_101_300001" in courses_by_id
    assert "112_1_101_300002" in courses_by_id
    assert "112_1_102_300003" not in courses_by_id

    course_full = courses_by_id["112_1_101_300001"]
    assert course_full["name"] == "Algorithms"
    assert course_full["code"] == "300001"
    assert course_full["credits"] == 3
    assert course_full["course_type"] == "Required"
    assert course_full["instructor"] == "Prof Turing"
    assert course_full["mon"] == "1-3"
    assert course_full["classroom"] == "Room 404"
    assert course_full["students_enrolled"] == 50
    assert course_full["students_dropped"] == 2
    assert course_full["language"] == "English"
    assert course_full["notes"] == "Prerequisite: Data Structures"
    assert course_full["with_class"] == "CS-A"
    assert course_full["experiment"] == "Lab 1"
    assert course_full["cross_discipline"] == "No"

    course_sparse = courses_by_id["112_1_101_300002"]
    assert course_sparse["name"] == "Data Structures"
    assert course_sparse["instructor"] == "Prof Knuth"
    assert course_sparse["classroom"] == "Room 405"
    assert course_sparse["students_enrolled"] == 45
    assert course_sparse["students_dropped"] == 0
    assert course_sparse["link"] is None
    assert course_sparse["notes"] is None


@pytest.mark.asyncio
async def test_get_courses_db_error(
    app_client: AsyncClient, test_db: DB, monkeypatch
):
    """Test /courses/courses handles DB errors by returning 500 via HTTP."""

    @asynccontextmanager
    async def broken_get_session():
        raise RuntimeError("DB error")
        yield  # pragma: no cover

    monkeypatch.setattr(test_db, "get_session", broken_get_session)

    response = await app_client.get(
        "/courses/courses", params={"department_year_id": "112_1_300_101"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")
