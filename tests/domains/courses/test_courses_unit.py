"""Unit tests for Courses domain router and schemas.

These tests run entirely in-memory using mocks for exec_mssql_async,
allowing thorough verification of endpoint contracts, return shapes,
Pydantic validation (including extra="forbid"), error handling, and 422 validations
without requiring a live MSSQL instance.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
import pydantic

from app.domains.courses.router import router as courses_router
from app.domains.courses.schemas import (
    CourseModel,
    CourseResponseSchema,
    CourseSyllabusModel,
    DepartmentModel,
    DepartmentResponseSchema,
    DepartmentYearModel,
    DepartmentYearResponseSchema,
    SemesterModel,
    SemesterResponseSchema,
)


@pytest.fixture
def test_courses_app() -> FastAPI:
    """Creates a FastAPI test app with courses router and bypassed cache dependencies."""
    app = FastAPI()

    async def dummy_cache_dep():
        yield

    for route in courses_router.routes:
        for dep in getattr(route, "dependencies", []):
            app.dependency_overrides[dep.dependency] = dummy_cache_dep

    app.include_router(courses_router)
    return app


@pytest_asyncio.fixture
async def courses_client(test_courses_app: FastAPI):
    """Provides an AsyncClient for test_courses_app."""
    async with AsyncClient(
        transport=ASGITransport(app=test_courses_app), base_url="http://test"
    ) as client:
        yield client


# ==============================================================================
# Endpoint: GET /courses/semesters
# ==============================================================================


@pytest.mark.asyncio
async def test_get_semesters_unit_success(courses_client: AsyncClient):
    """Test GET /courses/semesters returns list[SemesterResponseSchema] with exact shape."""
    mock_data = [
        {
            "id": "112_1",
            "year": "112",
            "sem": "1",
            "link": "Subj.jsp?year=112&sem=1",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
        },
        {
            "id": "112_2",
            "year": "112",
            "sem": "2",
            "link": "Subj.jsp?year=112&sem=2",
            "created_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2024, 6, 2, 12, 0, 0, tzinfo=UTC),
        },
    ]

    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=mock_data,
    ) as mock_exec:
        response = await courses_client.get("/courses/semesters")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Validate against response schema model
    validated = [SemesterResponseSchema.model_validate(item) for item in data]
    assert validated[0].id == "112_1"
    assert validated[0].year == "112"
    assert validated[0].sem == "1"
    assert validated[0].link == "Subj.jsp?year=112&sem=1"
    assert validated[1].id == "112_2"

    mock_exec.assert_awaited_once_with(command_name="courses/select_all_semester")


@pytest.mark.asyncio
async def test_get_semesters_unit_db_error(courses_client: AsyncClient):
    """Test GET /courses/semesters handles DB failure by returning 500 with Error ID."""
    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Database query timed out"),
    ):
        response = await courses_client.get("/courses/semesters")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")


# ==============================================================================
# Endpoint: GET /courses/departments
# ==============================================================================


@pytest.mark.asyncio
async def test_get_departments_unit_success(courses_client: AsyncClient):
    """Test GET /courses/departments returns list[DepartmentResponseSchema] with exact shape."""
    mock_data = [
        {
            "id": "112_1_300",
            "semester_id": "112_1",
            "year": "112",
            "sem": "1",
            "code": "300",
            "name": "Dept of Computer Science",
            "link": "Subj.jsp?year=112&sem=1&code=300",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
        }
    ]

    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=mock_data,
    ) as mock_exec:
        response = await courses_client.get(
            "/courses/departments", params={"semester_id": "112_1"}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    dept = DepartmentResponseSchema.model_validate(data[0])
    assert dept.id == "112_1_300"
    assert dept.semester_id == "112_1"
    assert dept.code == "300"
    assert dept.name == "Dept of Computer Science"

    mock_exec.assert_awaited_once_with("courses/select_department", "112_1")


@pytest.mark.asyncio
async def test_get_departments_unit_missing_param(courses_client: AsyncClient):
    """Test GET /courses/departments returns 422 when semester_id is missing."""
    response = await courses_client.get("/courses/departments")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    errors = response.json()["detail"]
    assert any(err.get("loc") == ["query", "semester_id"] for err in errors)


@pytest.mark.asyncio
async def test_get_departments_unit_db_error(courses_client: AsyncClient):
    """Test GET /courses/departments handles DB failure by returning 500 with Error ID."""
    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        side_effect=Exception("DB down"),
    ):
        response = await courses_client.get(
            "/courses/departments", params={"semester_id": "112_1"}
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"].startswith("Something went wrong! Error ID:")


# ==============================================================================
# Endpoint: GET /courses/department_years
# ==============================================================================


@pytest.mark.asyncio
async def test_get_department_years_unit_success(courses_client: AsyncClient):
    """Test GET /courses/department_years returns list[DepartmentYearResponseSchema] with exact shape."""
    mock_data = [
        {
            "id": "112_1_300_101",
            "department_id": "112_1_300",
            "year": "112",
            "sem": "1",
            "code": "101",
            "name": "CS Freshmen",
            "link": "Subj.jsp?year=112&sem=1&code=101",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
        }
    ]

    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=mock_data,
    ) as mock_exec:
        response = await courses_client.get(
            "/courses/department_years", params={"department_id": "112_1_300"}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    dy = DepartmentYearResponseSchema.model_validate(data[0])
    assert dy.id == "112_1_300_101"
    assert dy.department_id == "112_1_300"
    assert dy.code == "101"
    assert dy.name == "CS Freshmen"

    mock_exec.assert_awaited_once_with("courses/select_department_year", "112_1_300")


@pytest.mark.asyncio
async def test_get_department_years_unit_missing_param(courses_client: AsyncClient):
    """Test GET /courses/department_years returns 422 when department_id is missing."""
    response = await courses_client.get("/courses/department_years")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    errors = response.json()["detail"]
    assert any(err.get("loc") == ["query", "department_id"] for err in errors)


@pytest.mark.asyncio
async def test_get_department_years_unit_db_error(courses_client: AsyncClient):
    """Test GET /courses/department_years handles DB failure by returning 500 with Error ID."""
    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        side_effect=Exception("DB down"),
    ):
        response = await courses_client.get(
            "/courses/department_years", params={"department_id": "112_1_300"}
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"].startswith("Something went wrong! Error ID:")


# ==============================================================================
# Endpoint: GET /courses/courses
# ==============================================================================


@pytest.mark.asyncio
async def test_get_courses_unit_success(courses_client: AsyncClient):
    """Test GET /courses/courses returns list[CourseResponseSchema] with all 27 fields validated."""
    mock_data = [
        {
            "id": "112_1_101_300001",
            "department_year_id": "112_1_300_101",
            "year": "112",
            "sem": "1",
            "code": "300001",
            "name": "Operating Systems",
            "credits": 3,
            "course_type": "Required",
            "instructor": "Prof Dijkstra",
            "sun": None,
            "mon": "1-3",
            "tue": None,
            "wed": "2-4",
            "thu": None,
            "fri": None,
            "sat": None,
            "classroom": "Room 101",
            "students_enrolled": 40,
            "students_dropped": 1,
            "language": "English",
            "link": "Subj.jsp?course=300001",
            "notes": "Bring laptop",
            "with_class": "CS-A",
            "experiment": "Lab 1",
            "cross_discipline": "No",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
        }
    ]

    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=mock_data,
    ) as mock_exec:
        response = await courses_client.get(
            "/courses/courses", params={"department_year_id": "112_1_300_101"}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    course = CourseResponseSchema.model_validate(data[0])
    assert course.id == "112_1_101_300001"
    assert course.name == "Operating Systems"
    assert course.credits == 3
    assert course.instructor == "Prof Dijkstra"
    assert course.mon == "1-3"
    assert course.wed == "2-4"
    assert course.students_enrolled == 40
    assert course.students_dropped == 1

    mock_exec.assert_awaited_once_with("courses/select_courses", "112_1_300_101")


@pytest.mark.asyncio
async def test_get_courses_unit_missing_param(courses_client: AsyncClient):
    """Test GET /courses/courses returns 422 when department_year_id is missing."""
    response = await courses_client.get("/courses/courses")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    errors = response.json()["detail"]
    assert any(err.get("loc") == ["query", "department_year_id"] for err in errors)


@pytest.mark.asyncio
async def test_get_courses_unit_db_error(courses_client: AsyncClient):
    """Test GET /courses/courses handles DB failure by returning 500 with Error ID."""
    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        side_effect=Exception("DB down"),
    ):
        response = await courses_client.get(
            "/courses/courses", params={"department_year_id": "112_1_300_101"}
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"].startswith("Something went wrong! Error ID:")


# ==============================================================================
# Endpoint: GET /courses/syllabus
# ==============================================================================


@pytest.mark.asyncio
async def test_get_syllabus_unit_success(courses_client: AsyncClient):
    """Test GET /courses/syllabus returns single CourseSyllabusModel with exact shape."""
    mock_row = [
        {
            "id": "100_1_0078_153447_syllabus",
            "course_id": "100_1_0078_153447",
            "instructor_name": "王正豪",
            "email": "jhwang@ntut.edu.tw",
            "instructor_schedule": "星期一 10:00-12:00",
            "abstract": "Course overview",
            "syllabus": "Week 1: Introduction",
            "grading_policy": "Midterm 40%, Final 60%",
            "materials": "Required textbook",
            "consultation": "Office 402",
            "ai": "Allowed with citation",
            "notes": "Attendance required",
            "sdg": "Goal 4: Quality Education",
            "last_updated": datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC),
        }
    ]

    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=mock_row,
    ) as mock_exec:
        response = await courses_client.get(
            "/courses/syllabus", params={"course_id": "100_1_0078_153447"}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    syllabus = CourseSyllabusModel.model_validate(data)
    assert syllabus.id == "100_1_0078_153447_syllabus"
    assert syllabus.course_id == "100_1_0078_153447"
    assert syllabus.instructor_name == "王正豪"
    assert syllabus.email == "jhwang@ntut.edu.tw"
    assert syllabus.syllabus == "Week 1: Introduction"
    assert syllabus.grading_policy == "Midterm 40%, Final 60%"

    mock_exec.assert_awaited_once_with(
        "courses/select_syllabus", "100_1_0078_153447"
    )


@pytest.mark.asyncio
async def test_get_syllabus_unit_missing_param(courses_client: AsyncClient):
    """Test GET /courses/syllabus returns 422 when course_id query parameter is missing."""
    response = await courses_client.get("/courses/syllabus")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    errors = response.json()["detail"]
    assert any(err.get("loc") == ["query", "course_id"] for err in errors)


@pytest.mark.asyncio
async def test_get_syllabus_unit_not_one_row_raises_500(courses_client: AsyncClient):
    """Test GET /courses/syllabus raises 500 if database returns 0 or multiple rows."""
    # 0 rows returned
    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response_empty = await courses_client.get(
            "/courses/syllabus", params={"course_id": "unknown_course"}
        )
    assert response_empty.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_empty.json()["detail"].startswith(
        "Something went wrong! Error ID:"
    )

    # 2 rows returned
    with patch(
        "app.domains.courses.router.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=[{"id": "1"}, {"id": "2"}],
    ):
        response_multi = await courses_client.get(
            "/courses/syllabus", params={"course_id": "duplicate_course"}
        )
    assert response_multi.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_multi.json()["detail"].startswith(
        "Something went wrong! Error ID:"
    )


# ==============================================================================
# Schema Strictness and Shape Tests
# ==============================================================================


def test_course_response_schema_forbids_extra_fields():
    """Verify CourseResponseSchema enforces extra='forbid'."""
    valid_payload = {
        "id": "c1",
        "department_year_id": "dy1",
        "year": "112",
        "sem": "1",
        "name": "Course 1",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    # Valid
    model = CourseResponseSchema.model_validate(valid_payload)
    assert model.name == "Course 1"

    # Extra field should raise ValidationError
    with pytest.raises(pydantic.ValidationError):
        CourseResponseSchema.model_validate({**valid_payload, "unexpected_field": "disallowed"})


def test_semester_response_schema_forbids_extra_fields():
    """Verify SemesterResponseSchema enforces extra='forbid'."""
    valid_payload = {
        "id": "112_1",
        "year": "112",
        "sem": "1",
        "link": "Subj.jsp?year=112&sem=1",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    SemesterResponseSchema.model_validate(valid_payload)
    with pytest.raises(pydantic.ValidationError):
        SemesterResponseSchema.model_validate({**valid_payload, "extra": "boom"})


def test_department_response_schema_forbids_extra_fields():
    """Verify DepartmentResponseSchema enforces extra='forbid'."""
    valid_payload = {
        "id": "112_1_300",
        "semester_id": "112_1",
        "year": "112",
        "sem": "1",
        "code": "300",
        "name": "Dept CS",
        "link": "link",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    DepartmentResponseSchema.model_validate(valid_payload)
    with pytest.raises(pydantic.ValidationError):
        DepartmentResponseSchema.model_validate({**valid_payload, "extra": "boom"})


def test_department_year_response_schema_forbids_extra_fields():
    """Verify DepartmentYearResponseSchema enforces extra='forbid'."""
    valid_payload = {
        "id": "112_1_300_101",
        "department_id": "112_1_300",
        "year": "112",
        "sem": "1",
        "code": "101",
        "name": "Year 1",
        "link": "link",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    DepartmentYearResponseSchema.model_validate(valid_payload)
    with pytest.raises(pydantic.ValidationError):
        DepartmentYearResponseSchema.model_validate({**valid_payload, "extra": "boom"})


def test_course_syllabus_model_defaults_and_types():
    """Verify CourseSyllabusModel handles minimal inputs and optional fields default to None."""
    syllabus = CourseSyllabusModel(id="s1")
    assert syllabus.id == "s1"
    assert syllabus.course_id == ""
    assert syllabus.instructor_name is None
    assert syllabus.last_updated is None
