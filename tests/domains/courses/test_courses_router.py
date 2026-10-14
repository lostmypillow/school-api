from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables import Course, Department, DepartmentYear, Semester
from app.domains.courses.router import (
    get_course,
    get_departments,
    get_semesters,
    get_years,
)


@pytest.mark.asyncio
async def test_get_semesters_empty(app_client: AsyncClient):
    """Test /courses/semesters returns empty list when no data exists."""
    response = await app_client.get("/courses/semesters")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_semesters_with_data(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/semesters returns list of semesters when data exists."""
    sem1 = Semester(id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1")
    sem2 = Semester(id="112_2", year="112", sem="2", link="Subj.jsp?year=112&sem=2")
    test_session.add_all([sem1, sem2])
    await test_session.commit()

    response = await app_client.get("/courses/semesters")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    ids = {item["id"] for item in data}
    assert ids == {"112_1", "112_2"}
    assert data[0]["year"] == "112"


@pytest.mark.asyncio
async def test_get_semesters_db_error():
    """Test /courses/semesters handles DB session exceptions by raising 500 HTTPException."""
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock()
    mock_db.get_session.side_effect = RuntimeError("Database connection lost")
    mock_request.app.state.db = mock_db

    with pytest.raises(HTTPException) as exc_info:
        await get_semesters(mock_request)

    assert exc_info.value.status_code == 500
    assert "Something went wrong! Error ID:" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_departments_success(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/departments returns departments filtered by semester_id."""
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

    # Query matching semester
    response = await app_client.get(
        "/courses/departments", params={"semester_id": "112_1"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert {d["id"] for d in data} == {"112_1_300", "112_1_301"}

    # Query non-matching semester
    response_none = await app_client.get(
        "/courses/departments", params={"semester_id": "999_1"}
    )
    assert response_none.status_code == status.HTTP_200_OK
    assert response_none.json() == []


@pytest.mark.asyncio
async def test_get_departments_missing_param(app_client: AsyncClient):
    """Test /courses/departments returns 422 when semester_id is omitted."""
    response = await app_client.get("/courses/departments")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_departments_db_error():
    """Test /courses/departments raises 500 when query fails."""
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock()
    mock_db.get_session.side_effect = RuntimeError("DB error")
    mock_request.app.state.db = mock_db

    with pytest.raises(HTTPException) as exc_info:
        await get_departments(mock_request, semester_id="112_1")

    assert exc_info.value.status_code == 500
    assert "Something went wrong! Error ID:" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_department_years_success(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/department_years returns department years filtered by department_id."""
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
    test_session.add_all([sem, dep, dy1, dy2])
    await test_session.commit()

    response = await app_client.get(
        "/courses/department_years", params={"department_id": "112_1_300"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert {d["id"] for d in data} == {"112_1_300_101", "112_1_300_102"}


@pytest.mark.asyncio
async def test_get_department_years_missing_param(app_client: AsyncClient):
    """Test /courses/department_years returns 422 when department_id is omitted."""
    response = await app_client.get("/courses/department_years")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_department_years_db_error():
    """Test /courses/department_years raises 500 when query fails."""
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock()
    mock_db.get_session.side_effect = RuntimeError("DB error")
    mock_request.app.state.db = mock_db

    with pytest.raises(HTTPException) as exc_info:
        await get_years(mock_request, department_id="112_1_300")

    assert exc_info.value.status_code == 500
    assert "Something went wrong! Error ID:" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_courses_success(
    app_client: AsyncClient, test_session: AsyncSession
):
    """Test /courses/courses returns courses filtered by department_year_id."""
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
    dy = DepartmentYear(
        id="112_1_300_101",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="101",
        name="CS Year 1",
        link="Subj.jsp?year=112&sem=1&code=101",
    )
    c1 = Course(
        id="112_1_101_300001",
        department_year_id="112_1_300_101",
        year="112",
        sem="1",
        code="300001",
        name="Algorithms",
        credits=3,
        instructor="Prof Turing",
        classroom="Room 404",
        students_enrolled=50,
        students_dropped=2,
    )
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
    test_session.add_all([sem, dep, dy, c1, c2])
    await test_session.commit()

    response = await app_client.get(
        "/courses/courses", params={"department_year_id": "112_1_300_101"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert {c["id"] for c in data} == {"112_1_101_300001", "112_1_101_300002"}
    names = {c["name"] for c in data}
    assert names == {"Algorithms", "Data Structures"}


@pytest.mark.asyncio
async def test_get_courses_missing_param(app_client: AsyncClient):
    """Test /courses/courses returns 422 when department_year_id is omitted."""
    response = await app_client.get("/courses/courses")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_courses_db_error():
    """Test /courses/courses raises 500 when query fails."""
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock()
    mock_db.get_session.side_effect = RuntimeError("DB error")
    mock_request.app.state.db = mock_db

    with pytest.raises(HTTPException) as exc_info:
        await get_course(mock_request, department_year_id="112_1_300_101")

    assert exc_info.value.status_code == 500
    assert "Something went wrong! Error ID:" in exc_info.value.detail
